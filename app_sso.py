"""
====================================================================
项目名称：Special Deal 智能向导系统 (Phase 1 Intake)
当前版本：V2.0 - 核心功能：集成试剂明细网格 (Reagent Grid) 与动态求和
====================================================================
"""

import streamlit as st
import pandas as pd

# ==========================================
# 模块 1：主数据底表缓存层 (Master Data)
# ==========================================
@st.cache_data(ttl=600)
def get_master_data():
    """经销商白名单底表 (模拟从后台数据库或 Excel 获取)"""
    return pd.DataFrame({
        "Distributor_Code": ["D1001", "D1002", "ROCHE001"],
        "Distributor_Name": ["测试经销商A", "海安医学代理", "罗氏直销队伍"],
        "Status": ["Active", "Active", "Active"]
    })

@st.cache_data(ttl=600)
def get_reagent_master_data():
    """试剂货号、名称与标准指导价底表"""
    return pd.DataFrame({
        "Item_Code": ["7153414190", "7153716190", "0811122233", "0922233344"],
        "Product_Name": ["PT 试剂 (凝血酶原时间)", "PTT 试剂 (活化部分凝血活酶时间)", "Trop T HS (高敏肌钙蛋白)", "NT-proBNP (N端心房肽)"],
        "Product_Line": ["COAG", "COAG", "CARDIAC", "CARDIAC"],
        "Tests_Per_Kit": [354, 600, 100, 100],
        "Standard_Price_Tax_Inc": [1.17, 0.67, 25.50, 45.00]
    })

# ==========================================
# 模块 2：企业级安全双重鉴权 (SSO + Secrets Token 校验)
# 职责：结合平台保险箱，彻底拦截伪造邮箱后缀的攻击行为，实现零成本高安全闭环
# ==========================================
def verify_enterprise_sso():
    st.sidebar.title("🔐 罗氏内部系统鉴权")
    st.sidebar.caption("🔒 本系统已启用双因子安全凭证校验")
    
    # 1. 邮箱基础校验
    raw_email = st.sidebar.text_input("1. 请输入您的公司邮箱 *", placeholder="name@roche.com").strip().lower()
    
    # 2. 专属安全凭证 (Userid/Token) 校验
    user_token = st.sidebar.text_input("2. 请输入您的USER ID *", type="password", placeholder="例如: ROCHE-1234").strip()
    
    # 未输入完整时的友好引导
    if not raw_email or not user_token:
        st.info("👋 **安全访问限制：**\n\n为了保护企业商业数据，请在左侧栏输入您的 **罗氏公司邮箱** 及 **USER ID** 以解锁系统。")
        st.stop()
        
    # 拦截 1：检测邮箱后缀是否合法
    if not raw_email.endswith(("@roche.com", "@roche.com.cn", "@roche.ch")):
        st.sidebar.error("❌ 拒绝访问：非罗氏内部域邮箱")
        st.stop()
        
    # 拦截 2：【最核心安全检查】去 Streamlit 隐形保险箱里核对邮箱和 
    是否真实匹配！
    # 如果开发者还没有在云端配置 secrets，则给予安全降级防错提示
    if "auth_users" in st.secrets:
        valid_users = st.secrets["auth_users"]
        # 核对邮箱是否在白名单里，且密码完全一致
        if raw_email not in valid_users or valid_users[raw_email] != user_token:
            st.sidebar.error("❌ 鉴权失败：邮箱不存在或安全 USER ID错误！")
            st.error("""
            ### 🚨 非法登录拦截
            系统后台未检索到您的邮箱凭证，或您输入的 USER ID不正确。
            - 如果您是新加入内测的同仁，请联系项目负责人（系统管理员）申请在云端白名单中开通您的访问权限。
            """)
            st.stop()
    else:
        st.sidebar.warning("⚠️ 管理员未配置云端 Secrets，当前处于本地测试放行模式")
        
    # 验证全部完美通过！
    st.sidebar.success(f"✅ 身份验证成功\n\n**在线专家:** `{raw_email}`")
    return raw_email
# ==========================================
# 模块 3：经销商 Deal 绑定模块 (Deal Info)
# ==========================================
def render_deal_header():
    st.subheader("2. Deal 信息绑定 (Deal Info)")
    df_master = get_master_data()
    c1, c2 = st.columns(2)
    with c1:
        dist_code = st.text_input("经销商代码 *", placeholder="试试输入: D1001").strip().upper()
    with c2:
        dist_name = ""
        is_valid = False
        if dist_code:
            match = df_master[df_master["Distributor_Code"] == dist_code]
            if not match.empty and match.iloc[0]["Status"] == "Active":
                dist_name = match.iloc[0]["Distributor_Name"]
                is_valid = True
                st.success("✅ 经销商核实有效")
            else:
                st.error("❌ 代码不存在或已冻结，请核查")
        st.text_input("经销商名称 (系统自动联想/锁定)", value=dist_name, disabled=True)
    return is_valid

# ==========================================
# 模块 4：【核心功能】试剂动态网格引擎 (Reagent Grid)
# ==========================================
def render_reagent_grid():
    st.divider()
    st.subheader("4. 试剂明细录入 (Reagent Line Items)")
    st.caption("💡 操作提示：录入有效试剂货号（例如 `7153414190` 或 `0811122233`），系统会自动联想名称、锁定指导价并动态求和。")
    
    # 利用 Session State 在内存中构建虚拟表单行记录
    if "reagent_rows" not in st.session_state:
        st.session_state.reagent_rows = [{"code": "", "tests": 10000, "price": 0.0}]

    df_reagent = get_reagent_master_data()
    total_deal_revenue = 0.0
    
    # 循环渲染每一行动态网格
    for i, row in enumerate(st.session_state.reagent_rows):
        st.markdown(f"**第 {i+1} 行试剂**")
        c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 1.2, 1.2, 1.5, 1.8])
        
        with c1:
            code_input = st.text_input(f"货号 (Item Code) #{i+1}", value=row["code"], key=f"c_{i}").strip()
            st.session_state.reagent_rows[i]["code"] = code_input
            
        # 实时 VLOOKUP 联想底表数据
        match = df_reagent[df_reagent["Item_Code"] == code_input]
        if not match.empty:
            p_name = match.iloc[0]["Product_Name"]
            p_line = match.iloc[0]["Product_Line"]
            p_kit = match.iloc[0]["Tests_Per_Kit"]
            p_std_price = match.iloc[0]["Standard_Price_Tax_Inc"]
        else:
            p_name = "请填写有效货号..." if not code_input else "未识别货号"
            p_line = "-"
            p_kit = 0
            p_std_price = 0.0

        with c2:
            st.text_input(f"产品名称 (只读) #{i+1}", value=p_name, disabled=True, key=f"n_{i}")
        with c3:
            st.text_input(f"产品线 #{i+1}", value=p_line, disabled=True, key=f"l_{i}")
        with c4:
            st.text_input(f"Tests/Kit #{i+1}", value=str(p_kit), disabled=True, key=f"k_{i}")
        with c5:
            tests_input = st.number_input(f"预计年测试量 #{i+1}", min_value=0, step=1000, value=row["tests"], key=f"t_{i}")
            st.session_state.reagent_rows[i]["tests"] = tests_input
        with c6:
            # 业务员未修改单价时，自动注入含税指导单价
            def_price = p_std_price if row["price"] == 0.0 else row["price"]
            price_input = st.number_input(f"申请含税单价(¥) #{i+1}", min_value=0.0, step=0.1, value=float(def_price), key=f"p_{i}")
            st.session_state.reagent_rows[i]["price"] = price_input
            
        # 实时计算当前行的年总收入
        row_rev = tests_input * price_input
        total_deal_revenue += row_rev
        st.write(f"↳ *此行标准指导价: ¥{p_std_price} | 预估此项年贡献: **¥ {row_rev:,.2f}***")
        st.write("---")

    # 动态增删操作行按钮区
    btn1, btn2, _ = st.columns([1.5, 1.5, 6])
    with btn1:
        if st.button("➕ 追加一行试剂", type="secondary"):
            st.session_state.reagent_rows.append({"code": "", "tests": 10000, "price": 0.0})
            st.rerun()
    with btn2:
        if len(st.session_state.reagent_rows) > 1:
            if st.button("🗑️ 移除底部一行", type="secondary"):
                st.session_state.reagent_rows.pop()
                st.rerun()
                
    # 顶部及底部大盘财务指标输出
    st.info(f"📈 **当前 Deal 试剂预估年总收入 (Total Estimated Annual Revenue)： ¥ {total_deal_revenue:,.2f}**")

# ==========================================
# 模块 5：系统启动主流程
# ==========================================
if __name__ == "__main__":
    st.set_page_config(page_title="Special Deal Intake", page_icon="📋", layout="wide")
    user = verify_enterprise_sso()
    st.title("📋 Special Deal 智能向导申请系统")
    st.caption(f"当前在线操作人: {user} | 运行环境: Streamlit Zero-Server Cloud")
    st.divider()
    
    # 权限互锁：只有输入有效经销商代码后，才展示试剂录入表格
    if render_deal_header():
        render_reagent_grid()
    else:
        st.warning("⚠️ 权限互锁提示：请先在上方的 Deal 信息面板中输入有效的【经销商代码】以解锁试剂明细网格！")