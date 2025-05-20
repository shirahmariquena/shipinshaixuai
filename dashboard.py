import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import tempfile
from mock_pipeline import MockPipeline
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Dashboard")

def main():
    """Streamlit app for candidate video analysis"""
    st.title("候选人视频分析仪表板")
    
    # Create sidebar for navigation
    page = st.sidebar.selectbox(
        "选择页面",
        ["上传视频", "分析结果", "候选人比较"]
    )
    
    if page == "上传视频":
        show_upload_page()
    elif page == "分析结果":
        show_analysis_page()
    elif page == "候选人比较":
        show_comparison_page()

def show_upload_page():
    """Page for uploading candidate videos"""
    st.header("上传候选人视频")
    
    # File uploader
    uploaded_file = st.file_uploader("选择视频文件", type=["mp4", "mov", "avi"])
    
    if uploaded_file is not None:
        # Create a temporary file to save the video
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name
        tfile.close()
        
        # Display the video
        st.video(video_path)
        
        # Metadata form
        with st.form("candidate_metadata"):
            st.write("输入候选人信息")
            candidate_name = st.text_input("候选人姓名")
            position = st.text_input("应聘职位")
            job_keywords = st.text_input("职位关键词（逗号分隔）")
            
            # Form submission
            submitted = st.form_submit_button("处理视频")
            if submitted:
                try:
                    # 显示处理进度
                    st.success(f"开始处理 {candidate_name} 的视频...")
                    
                    # 显示进度条
                    progress_bar = st.progress(0)
                    for i in range(100):
                        import time
                        time.sleep(0.05)
                        progress_bar.progress(i + 1)
                    
                    # 使用模拟管道进行处理
                    pipeline = MockPipeline(logger=logger)
                    job_keywords_list = [keyword.strip() for keyword in job_keywords.split(",")] if job_keywords else []
                    result = pipeline.process_video(video_path, job_keywords_list, candidate_name)
                    
                    # 将结果存储在session_state中，以便在其他页面使用
                    if 'candidates' not in st.session_state:
                        st.session_state.candidates = {}
                    
                    st.session_state.candidates[candidate_name] = result
                    st.session_state.selected_candidate = candidate_name
                    
                    st.success("视频处理完成！")
                    st.info("请前往'分析结果'页面查看详细分析。")
                    
                except Exception as e:
                    st.error(f"处理视频时出错: {str(e)}")
                finally:
                    # Clean up the temporary file
                    if os.path.exists(video_path):
                        os.unlink(video_path)

def show_analysis_page():
    """Page for displaying analysis results"""
    st.header("候选人分析结果")
    
    # 如果没有候选人数据，则创建模拟数据
    if 'candidates' not in st.session_state or not st.session_state.candidates:
        # Create sample data for demonstration
        mock_pipeline = MockPipeline()
        candidates = ["张三", "李四", "王五", "赵六"]
        st.session_state.candidates = {}
        
        for candidate in candidates:
            result = mock_pipeline.process_video("示例视频.mp4", ["技术", "开发", "编程"], candidate)
            st.session_state.candidates[candidate] = result
    
    # 选择候选人
    candidate_names = list(st.session_state.candidates.keys())
    selected_candidate = st.selectbox("选择候选人", candidate_names)
    
    # 获取所选候选人的数据
    candidate_data = st.session_state.candidates[selected_candidate]
    scores = candidate_data['scores']
    
    # 显示候选人详细信息
    st.subheader(f"{selected_candidate}的分析")
    
    # 创建雷达图
    feature_scores = scores['feature_scores']
    categories = list(feature_scores.keys())
    values = list(feature_scores.values())
    
    # 将分数缩放到0-1范围
    normalized_values = [v/100 for v in values]
    
    # 使用Plotly创建雷达图
    fig = px.line_polar(
        r=normalized_values,
        theta=categories,
        line_close=True,
        range_r=[0, 1],
        title=f"{selected_candidate}的评估分数"
    )
    st.plotly_chart(fig)
    
    # 显示总体分数
    st.metric("总体分数", f"{scores['overall_score']:.2f} / 100.00")
    
    # 显示各组件分数
    col1, col2, col3 = st.columns(3)
    col1.metric("视觉分析", f"{scores['component_scores']['visual']:.2f}")
    col2.metric("音频分析", f"{scores['component_scores']['audio']:.2f}")
    col3.metric("内容分析", f"{scores['component_scores']['content']:.2f}")
    
    # 显示各个特征分数
    st.subheader("详细特征分数")
    cols = st.columns(2)
    for i, (category, value) in enumerate(feature_scores.items()):
        cols[i % 2].metric(category.replace("_", " ").title(), f"{value:.2f}")
    
    # 显示优势和改进建议
    st.subheader("优势与改进")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**优势:**")
        for strength in scores['strengths']:
            st.success(f"- {strength.replace('_', ' ').title()}")
    
    with col2:
        st.write("**改进建议:**")
        if scores['improvements']:
            for improvement in scores['improvements']:
                st.warning(f"- {improvement.replace('_', ' ').title()}")
        else:
            st.info("- 没有明显需要改进的地方")
    
    # 显示转录文本
    st.subheader("语音转录")
    st.text_area("转录内容", candidate_data['transcript'], height=150)

def show_comparison_page():
    """Page for comparing multiple candidates"""
    st.header("候选人比较")
    
    # 如果没有候选人数据，则创建模拟数据
    if 'candidates' not in st.session_state or not st.session_state.candidates:
        # Create sample data for demonstration
        mock_pipeline = MockPipeline()
        candidates = ["张三", "李四", "王五", "赵六"]
        st.session_state.candidates = {}
        
        for candidate in candidates:
            result = mock_pipeline.process_video("示例视频.mp4", ["技术", "开发", "编程"], candidate)
            st.session_state.candidates[candidate] = result
    
    # 准备比较数据
    candidates = list(st.session_state.candidates.keys())
    
    # 提取分数数据
    data = []
    for name in candidates:
        candidate_data = st.session_state.candidates[name]
        scores = candidate_data['scores']
        
        row = {
            'candidate': name,
            'overall_score': scores['overall_score'],
            'visual': scores['component_scores']['visual'],
            'audio': scores['component_scores']['audio'],
            'content': scores['component_scores']['content']
        }
        
        # 添加特征分数
        for feature, value in scores['feature_scores'].items():
            row[feature] = value
            
        data.append(row)
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 按总分排序
    df = df.sort_values("overall_score", ascending=False)
    
    # 显示比较表格
    st.dataframe(df)
    
    # 创建总分条形图
    fig = px.bar(
        df, 
        x="candidate", 
        y="overall_score",
        title="候选人总体分数",
        labels={"candidate": "候选人", "overall_score": "总体分数"}
    )
    st.plotly_chart(fig)
    
    # 让用户选择要比较的分数
    score_options = list(scores['feature_scores'].keys())
    selected_scores = st.multiselect(
        "选择要比较的特征",
        score_options,
        default=["job_relevance", "confidence"]
    )
    
    if selected_scores:
        # 创建分组条形图进行比较
        comparison_df = pd.melt(
            df, 
            id_vars=["candidate"], 
            value_vars=selected_scores,
            var_name="metric", 
            value_name="score"
        )
        
        fig = px.bar(
            comparison_df,
            x="candidate",
            y="score",
            color="metric",
            barmode="group",
            title="特定指标比较",
            labels={"candidate": "候选人", "score": "分数", "metric": "指标"}
        )
        st.plotly_chart(fig)

if __name__ == "__main__":
    main()
