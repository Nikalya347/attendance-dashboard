import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Enhanced Student Attendance Analytics",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Advanced Student Attendance & Risk Analytics System")
st.markdown(
    "An executive dashboard for cohort risk management, student lookup, and"
    " reporting."
)


# 2. Data Loading Function with Cache
@st.cache_data
def load_data():
  file_path = "attendance_data.xlsx"
  df_audit = pd.read_excel(file_path, sheet_name="Cohort Compliance Audit")
  df_trends = pd.read_excel(file_path, sheet_name="Daily Session Trends")
  return df_audit, df_trends


try:
  df_audit, df_trends = load_data()

  # --- Global Sidebar Filters ---
  st.sidebar.header("🔍 Global Filters")

  gender_filter = st.sidebar.multiselect(
      "Filter by Gender:",
      options=df_audit["Gender"].unique(),
      default=df_audit["Gender"].unique(),
  )

  risk_filter = st.sidebar.multiselect(
      "Filter by Risk Tier:",
      options=df_audit["Risk Tier"].unique(),
      default=df_audit["Risk Tier"].unique(),
  )

  # Filtered Base Dataset
  filtered_df = df_audit[
      (df_audit["Gender"].isin(gender_filter))
      & (df_audit["Risk Tier"].isin(risk_filter))
  ]

  # --- Top KPI Summary Bar ---
  total_students = len(filtered_df)
  critical_count = len(
      filtered_df[filtered_df["Risk Tier"] == "Critical Risk"]
  )
  avg_attendance = (
      filtered_df["Overall Attendance %"].mean() if total_students > 0 else 0
  )
  avg_safe_skips = (
      filtered_df["Safe Skips"].mean() if total_students > 0 else 0
  )

  kpi1, kpi2, kpi3, kpi4 = st.columns(4)
  kpi1.metric("Selected Students", total_students)
  kpi2.metric(
      "Critical Risk Count", critical_count, delta_color="inverse"
  )
  kpi3.metric("Average Attendance", f"{avg_attendance:.1f}%")
  kpi4.metric("Avg Safe Skips Left", f"{avg_safe_skips:.1f} sessions")

  st.divider()

  # --- Tabbed Navigation Layout ---
  tab1, tab2, tab3, tab4 = st.tabs([
      "📊 Cohort Overview",
      "👤 Individual Student Lookup",
      "📈 Time & Weekday Trends",
      "📋 Data Inspector & Export",
  ])

  # ==========================================
  # TAB 1: COHORT OVERVIEW
  # ==========================================
  with tab1:
    st.header("Overview & Risk Segmentation")
    col1, col2 = st.columns(2)

    with col1:
      st.subheader("📌 Risk Tier Distribution")
      risk_fig = px.pie(
          filtered_df,
          names="Risk Tier",
          color="Risk Tier",
          color_discrete_map={"Safe": "#2ecc71", "Critical Risk": "#e74c3c"},
          hole=0.4,
      )
      st.plotly_chart(risk_fig, use_container_width=True)

    with col2:
      st.subheader("🔬 Theory vs. Lab Attendance")
      scatter_fig = px.scatter(
          filtered_df,
          x="Theory %",
          y="Lab %",
          color="Risk Tier",
          hover_data=["Student Name", "Register No", "Safe Skips"],
          color_discrete_map={"Safe": "#2ecc71", "Critical Risk": "#e74c3c"},
      )
      scatter_fig.add_hline(
          y=75, line_dash="dash", line_color="gray", annotation_text="75% Min"
      )
      scatter_fig.add_vline(
          x=75, line_dash="dash", line_color="gray", annotation_text="75% Min"
      )
      st.plotly_chart(scatter_fig, use_container_width=True)

    # Deficient Courses Analysis
    st.subheader("⚠️ Deficient Courses Breakdown")
    deficient_df = filtered_df[filtered_df["Deficient Courses"].notna()]
    if not deficient_df.empty:
      course_counts = (
          deficient_df["Deficient Courses"].value_counts().reset_index()
      )
      course_counts.columns = ["Course Code", "Affected Students"]
      fig_def = px.bar(
          course_counts,
          x="Course Code",
          y="Affected Students",
          color="Affected Students",
          color_continuous_scale="Reds",
          title="Number of Students At Risk per Course",
      )
      st.plotly_chart(fig_def, use_container_width=True)
    else:
      st.info("No course deficiencies found in the current filter selection.")

  # ==========================================
  # TAB 2: INDIVIDUAL STUDENT LOOKUP
  # ==========================================
  with tab2:
    st.header("👤 Individual Student Health Card")

    student_list = df_audit["Student Name"].tolist()
    selected_student = st.selectbox(
        "Select or Search Student Name:", options=student_list
    )

    student_data = df_audit[
        df_audit["Student Name"] == selected_student
    ].iloc[0]

    # Student Details Cards
    card_col1, card_col2, card_col3 = st.columns(3)
    card_col1.markdown(f"**Register No:** `{student_data['Register No']}`")
    card_col1.markdown(f"**Gender:** {student_data['Gender']}")

    risk_color = "🔴" if student_data["Risk Tier"] == "Critical Risk" else "🟢"
    card_col2.markdown(
        f"**Risk Tier:** {risk_color} **{student_data['Risk Tier']}**"
    )
    card_col2.markdown(
        f"**Overall Attendance:** `{student_data['Overall Attendance %']}%`"
    )

    card_col3.markdown(
        f"**Safe Skips Remaining:** `{student_data['Safe Skips']}`"
    )
    card_col3.markdown(
        f"**Recovery Sessions Needed:** `{student_data['Recovery Needed']}`"
    )

    st.subheader("Attendance Breakdown")
    breakdown_df = pd.DataFrame({
        "Metric": ["Theory %", "Lab %", "Projected % (to LWD)"],
        "Percentage": [
            student_data["Theory %"],
            student_data["Lab %"],
            student_data["Projected % (to LWD)"],
        ],
    })
    fig_student = px.bar(
        breakdown_df,
        x="Metric",
        y="Percentage",
        text="Percentage",
        color="Percentage",
        color_continuous_scale="Viridis",
        range_y=[0, 100],
    )
    st.plotly_chart(fig_student, use_container_width=True)

  # ==========================================
  # TAB 3: TIME & WEEKDAY TRENDS
  # ==========================================
  with tab3:
    st.header("📈 Attendance Patterns & Temporal Analysis")

    trend_col1, trend_col2 = st.columns(2)

    with trend_col1:
      st.subheader("Daily Attendance Trend")
      df_trends["Date"] = pd.to_datetime(df_trends["Date"])
      line_fig = px.line(
          df_trends,
          x="Date",
          y="Attendance %",
          title="Daily Cohort Attendance Over Time",
      )
      line_fig.add_hline(
          y=85,
          line_dash="dash",
          line_color="orange",
          annotation_text="Target Threshold (85%)",
      )
      st.plotly_chart(line_fig, use_container_width=True)

    with trend_col2:
      st.subheader("Average Absentees by Weekday")
      day_order = [
          "Monday",
          "Tuesday",
          "Wednesday",
          "Thursday",
          "Friday",
          "Saturday",
      ]
      avg_absent = (
          df_trends.groupby("Day")["Total Absentees"]
          .mean()
          .reindex(day_order)
          .reset_index()
      )
      bar_fig = px.bar(
          avg_absent,
          x="Day",
          y="Total Absentees",
          color="Total Absentees",
          color_continuous_scale="Blues",
      )
      st.plotly_chart(bar_fig, use_container_width=True)

  # ==========================================
  # TAB 4: DATA INSPECTOR & EXPORT
  # ==========================================
  with tab4:
    st.header("📋 Interactive Data Inspector & Export")

    st.subheader("Filtered Student Table")
    st.dataframe(filtered_df, use_container_width=True)

    st.divider()
    st.subheader("📥 Export Data")

    # Convert dataframe to CSV for download
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📄 Download Filtered Data as CSV",
        data=csv_data,
        file_name="student_attendance_filtered_report.csv",
        mime="text/csv",
    )

except Exception as e:
  st.error(
      f"Please verify 'attendance_data.xlsx' is in your project directory."
      f" Error details: {e}"
  )