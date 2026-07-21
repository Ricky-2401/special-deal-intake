"""
====================================================================
项目名称：Special Deal 智能申请系统 (兼容 SSO 与云迁移架构)
职责：实现企业邮箱 SSO 鉴权、经销商代码动态核对及主数据绑定
====================================================================
"""

import streamlit as st
import pandas as pd

# ==========================================
# 模块 1：数据适配器 (Data Adapter Pattern)
# ==========================================
@st.cache_data(ttl=600)
def get_master_data(platform="Google"):
    """
    数据获取路由函数：目前模拟 Google Drive 中的主数据，未来可一键切换至微软生态
    """
    if platform == "Google":
        # 模拟我们主数据表里的【经销商清单】
        data = {
            "Distributor_Code": ["D1001", "D1002", "ROCHE001"],
            "Distributor_Name": ["测试经销商", "海安代理", "罗氏直销线"],
            "Status": ["Active", "Active", "Active"]
        }
        return pd.DataFrame(data)
    else:
        raise ValueError("不支持的数据平台参数！")

# ==========================================
# 模块 2：企业单点登录鉴权 (SSO Authentication)
# ==========================================
# ==========================================
# 模块 2：企业单点登录鉴权 (SSO Authentication) - 升级版
# 职责：支持多域名白名单校验，准确识别罗氏内部员工身份
# ==========================================
def verify_enterprise_sso():
    """
    企业级 SSO 验证逻辑：核对登录用户的企业邮箱后缀，确保系统信息安全
    """
    st.sidebar.title("🔐 企业身份验证")
    
    # 【参数调整区】将这里改为了元组 (Tuple)，可以同时授权多个罗氏的合法尾缀！
    ALLOWED_DOMAINS = ("@roche.com", "@roche.com.cn", "@roche.ch") 
    
    # 模拟 SSO 抓取到的用户邮箱
    user_email = st.sidebar.text_input("企业邮箱登录鉴权 (SSO Simulation):", placeholder="例如: ricky.xu@roche.com")
    
    if not user_email:
        st.info("👋 欢迎访问 Special Deal 申请平台。\n请先在左侧侧边栏输入您的企业邮箱完成鉴权解锁。")
        st.stop()
        
    # 技能点：在 Python 中，endswith() 函数如果接收一个元组，会自动检查邮箱是不是以其中任意一个域名结尾！
    if not user_email.lower().strip().endswith(ALLOWED_DOMAINS):
        st.error(f"❌ 权限拒绝：您的账号 ({user_email}) 不在公司内部授权域名白名单 {ALLOWED_DOMAINS} 内！")
        st.stop()
        
    st.sidebar.success(f"✅ 鉴权成功\n欢迎罗氏同仁：{user_email}")
    return user_email
# ==========================================
# 模块 3：在线申请表单 - 第 2 步 Deal 交易信息
# ==========================================
def render_deal_header(current_user):
    st.title("📋 Special Deal 申请 - Phase 1 Intake")
    st.caption(f"当前登录操作员：{current_user} | 底层数据引擎：Google Workspace 实时同步")
    st.divider()
    
    df_master = get_master_data(platform="Google")
    st.subheader("2. Deal 信息 (Deal Info)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 业务员录入经销商代码
        dist_code = st.text_input("经销商代码 (Distributor code) *", placeholder="试试输入：D1001 或 ROCHE001").strip().upper()
        
    with col2:
        dist_name = ""
        is_verified = False
        
        if dist_code:
            # 采用后台核对算法查找主数据
            match = df_master[df_master["Distributor_Code"] == dist_code]
            
            if not match.empty:
                if match.iloc[0]["Status"] == "Active":
                    dist_name = match.iloc[0]["Distributor_Name"]
                    is_verified = True
                    st.success("✅ 验证通过！主数据已匹配。")
                else:
                    st.error("⚠️ 该经销商代码已被冻结，无法受理！")
            else:
                st.error("❌ 系统找不到对应的经销商代码，请核实！")
                
        # 渲染【只读不可修改】的名称框，彻底解决人工录入错误的痛点
        st.text_input("经销商名称 (Distributor L1 name) - 自动联想/不可修改 *", value=dist_name, disabled=True)
        
    st.divider()
    if is_verified:
        st.button("验证完毕，下一步：试剂与仪器明细录入 ➔", type="primary")
    else:
        st.button("验证完毕，下一步：试剂与仪器明细录入 ➔", disabled=True)

if __name__ == "__main__":
    st.set_page_config(page_title="Special Deal Intake", page_icon="📑", layout="wide")
    logged_in_user = verify_enterprise_sso()
    render_deal_header(logged_in_user)