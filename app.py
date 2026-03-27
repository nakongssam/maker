import os
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(page_title="메이커 동아리 관리 앱", page_icon="🛠️", layout="wide")

DATA_DIR = "data"
STUDENTS_FILE = os.path.join(DATA_DIR, "students.csv")
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.csv")
CAREER_FILE = os.path.join(DATA_DIR, "career.csv")

DEFAULT_CAREER_OPTIONS = [
    "미정",
    "기계/자동차",
    "전기/전자",
    "AI/소프트웨어",
    "디자인",
    "창업",
    "대학 진학",
    "공무원/공기업",
    "기타",
]


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


@st.cache_data
def load_csv(path: str, columns: list[str]) -> pd.DataFrame:
    if os.path.exists(path):
        df = pd.read_csv(path)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[columns]
    return pd.DataFrame(columns=columns)


@st.cache_data
def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")



def save_df(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False, encoding="utf-8-sig")
    load_csv.clear()
    convert_df_to_csv.clear()



def init_data():
    ensure_data_dir()
    students_cols = ["학번", "이름", "학년", "반", "비고"]
    attendance_cols = ["날짜", "학번", "이름", "출석상태", "메모"]
    career_cols = ["학번", "이름", "희망진로", "관심분야", "희망학과/직업", "상담필요", "메모"]

    if "students_df" not in st.session_state:
        st.session_state.students_df = load_csv(STUDENTS_FILE, students_cols)
    if "attendance_df" not in st.session_state:
        st.session_state.attendance_df = load_csv(ATTENDANCE_FILE, attendance_cols)
    if "career_df" not in st.session_state:
        st.session_state.career_df = load_csv(CAREER_FILE, career_cols)



def sync_student_names():
    students_df = st.session_state.students_df.copy()
    career_df = st.session_state.career_df.copy()

    if students_df.empty:
        return

    if career_df.empty:
        career_df = pd.DataFrame(columns=["학번", "이름", "희망진로", "관심분야", "희망학과/직업", "상담필요", "메모"])

    merged = students_df[["학번", "이름"]].copy()
    merged = merged.merge(career_df, on=["학번", "이름"], how="left")
    merged["희망진로"] = merged["희망진로"].fillna("미정")
    merged["관심분야"] = merged["관심분야"].fillna("")
    merged["희망학과/직업"] = merged["희망학과/직업"].fillna("")
    merged["상담필요"] = merged["상담필요"].fillna(False)
    merged["메모"] = merged["메모"].fillna("")

    st.session_state.career_df = merged[["학번", "이름", "희망진로", "관심분야", "희망학과/직업", "상담필요", "메모"]]



def main_header():
    st.title("🛠️ 메이커 동아리 관리 웹앱")
    st.caption("학생 출석 확인과 진로 체크를 한 번에 관리하는 Streamlit 앱")



def normalize_students_df(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = ["학번", "이름", "학년", "반", "비고"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

    df = df[required_cols].copy()
    df["학번"] = df["학번"].astype(str).str.strip()
    df["이름"] = df["이름"].astype(str).str.strip()
    df["비고"] = df["비고"].fillna("").astype(str)
    df["학년"] = pd.to_numeric(df["학년"], errors="coerce")
    df["반"] = pd.to_numeric(df["반"], errors="coerce")

    return df



def sidebar_controls():
    with st.sidebar:
        st.header("⚙️ 관리 메뉴")
        st.write("필요한 데이터를 업로드하거나 샘플 파일을 내려받을 수 있습니다.")

        uploaded_students = st.file_uploader("학생 명단 CSV 업로드", type=["csv"])
        if uploaded_students is not None:
            df = pd.read_csv(uploaded_students)
            df = normalize_students_df(df)
            st.session_state.students_df = df
            save_df(st.session_state.students_df, STUDENTS_FILE)
            sync_student_names()
            save_df(st.session_state.career_df, CAREER_FILE)
            st.success("학생 명단을 불러왔습니다.")

        sample_students = pd.DataFrame(
            [
                {"학번": "10101", "이름": "김민준", "학년": 1, "반": 1, "비고": ""},
                {"학번": "10102", "이름": "이서연", "학년": 1, "반": 1, "비고": ""},
            ]
        )
        st.download_button(
            "학생 명단 샘플 CSV 다운로드",
            data=convert_df_to_csv(sample_students),
            file_name="students_sample.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.divider()
        if st.button("전체 데이터 저장", use_container_width=True):
            save_df(st.session_state.students_df, STUDENTS_FILE)
            save_df(st.session_state.attendance_df, ATTENDANCE_FILE)
            save_df(st.session_state.career_df, CAREER_FILE)
            st.success("모든 데이터를 저장했습니다.")

        if st.button("오늘 출석 초기화", use_container_width=True):
            today_str = str(date.today())
            st.session_state.attendance_df = st.session_state.attendance_df[
                st.session_state.attendance_df["날짜"] != today_str
            ]
            save_df(st.session_state.attendance_df, ATTENDANCE_FILE)
            st.warning("오늘 날짜의 출석 기록을 초기화했습니다.")



def students_tab():
    st.subheader("1) 학생 명단 관리")
    st.write("학생 기본 명단을 입력하거나 수정하세요.")

    editable_students = st.session_state.students_df.copy()
    editable_students["학년"] = pd.to_numeric(editable_students["학년"], errors="coerce")
    editable_students["반"] = pd.to_numeric(editable_students["반"], errors="coerce")

    edited_students = st.data_editor(
        editable_students,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="students_editor",
        column_config={
            "학번": st.column_config.TextColumn("학번"),
            "이름": st.column_config.TextColumn("이름"),
            "학년": st.column_config.NumberColumn("학년", min_value=1, max_value=3, step=1),
            "반": st.column_config.NumberColumn("반", min_value=1, max_value=20, step=1),
            "비고": st.column_config.TextColumn("비고"),
        },
    )

    if st.button("학생 명단 저장", key="save_students"):
        edited_students = normalize_students_df(edited_students)
        if edited_students["학번"].eq("").any() or edited_students["이름"].eq("").any():
            st.error("학번과 이름은 비워둘 수 없습니다.")
            return

        if edited_students["학년"].isna().any() or edited_students["반"].isna().any():
            st.error("학년과 반은 숫자로 입력해주세요.")
            return

        edited_students["학년"] = edited_students["학년"].astype(int)
        edited_students["반"] = edited_students["반"].astype(int)
        st.session_state.students_df = edited_students.drop_duplicates(subset=["학번"], keep="last")
        sync_student_names()
        save_df(st.session_state.students_df, STUDENTS_FILE)
        save_df(st.session_state.career_df, CAREER_FILE)
        st.success("학생 명단을 저장했습니다.")



def attendance_tab():
    st.subheader("2) 출석 체크")

    students_df = st.session_state.students_df.copy()
    if students_df.empty:
        st.info("먼저 학생 명단을 입력해주세요.")
        return

    selected_date = st.date_input("출석 날짜", value=date.today())
    selected_grade = st.selectbox("학년 선택", options=["전체"] + sorted(students_df["학년"].dropna().astype(int).unique().tolist()))

    filtered_students = students_df.copy()
    if selected_grade != "전체":
        filtered_students = filtered_students[filtered_students["학년"].astype(int) == int(selected_grade)]

    today_attendance = st.session_state.attendance_df.copy()
    today_attendance = today_attendance[today_attendance["날짜"] == str(selected_date)]

    base_df = filtered_students[["학번", "이름"]].copy()
    base_df["출석상태"] = "출석"
    base_df["메모"] = ""

    if not today_attendance.empty:
        base_df = base_df.merge(today_attendance[["학번", "출석상태", "메모"]], on="학번", how="left", suffixes=("", "_기존"))
        base_df["출석상태"] = base_df["출석상태_기존"].fillna(base_df["출석상태"])
        base_df["메모"] = base_df["메모_기존"].fillna(base_df["메모"])
        base_df = base_df[["학번", "이름", "출석상태", "메모"]]

    edited_attendance = st.data_editor(
        base_df,
        use_container_width=True,
        hide_index=True,
        key="attendance_editor",
        column_config={
            "학번": st.column_config.TextColumn("학번", disabled=True),
            "이름": st.column_config.TextColumn("이름", disabled=True),
            "출석상태": st.column_config.SelectboxColumn(
                "출석상태",
                options=["출석", "지각", "결석", "조퇴"],
                required=True,
            ),
            "메모": st.column_config.TextColumn("메모"),
        },
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("이 날짜 출석 저장", use_container_width=True):
            new_rows = edited_attendance.copy()
            new_rows.insert(0, "날짜", str(selected_date))
            remain_df = st.session_state.attendance_df[
                st.session_state.attendance_df["날짜"] != str(selected_date)
            ]
            st.session_state.attendance_df = pd.concat([remain_df, new_rows], ignore_index=True)
            save_df(st.session_state.attendance_df, ATTENDANCE_FILE)
            st.success(f"{selected_date} 출석을 저장했습니다.")

    with col2:
        summary = edited_attendance["출석상태"].value_counts().to_dict()
        st.metric("출석", summary.get("출석", 0))
    with col3:
        absent_like = summary.get("결석", 0) + summary.get("지각", 0) + summary.get("조퇴", 0)
        st.metric("출석 외", absent_like)

    st.markdown("### 최근 출석 기록")
    history_df = st.session_state.attendance_df.sort_values(by=["날짜", "학번"], ascending=[False, True])
    st.dataframe(history_df, use_container_width=True, hide_index=True)



def career_tab():
    st.subheader("3) 진로 체크")

    students_df = st.session_state.students_df.copy()
    if students_df.empty:
        st.info("먼저 학생 명단을 입력해주세요.")
        return

    sync_student_names()
    career_df = st.session_state.career_df.copy()

    search_name = st.text_input("학생 이름 검색", placeholder="이름을 입력하세요")
    view_mode = st.selectbox("상담필요 학생 보기", options=["전체", "상담필요만"])

    if search_name:
        career_df = career_df[career_df["이름"].astype(str).str.contains(search_name, na=False)]
    if view_mode == "상담필요만":
        career_df = career_df[career_df["상담필요"] == True]

    edited_career = st.data_editor(
        career_df,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key="career_editor",
        column_config={
            "학번": st.column_config.TextColumn("학번", disabled=True),
            "이름": st.column_config.TextColumn("이름", disabled=True),
            "희망진로": st.column_config.SelectboxColumn("희망진로", options=DEFAULT_CAREER_OPTIONS),
            "관심분야": st.column_config.TextColumn("관심분야"),
            "희망학과/직업": st.column_config.TextColumn("희망학과/직업"),
            "상담필요": st.column_config.CheckboxColumn("상담필요"),
            "메모": st.column_config.TextColumn("메모"),
        },
    )

    if st.button("진로 정보 저장", use_container_width=True):
        source_df = st.session_state.career_df.copy()
        update_ids = edited_career["학번"].astype(str).tolist()
        source_df["학번"] = source_df["학번"].astype(str)
        edited_career["학번"] = edited_career["학번"].astype(str)
        source_df = source_df[~source_df["학번"].isin(update_ids)]
        st.session_state.career_df = pd.concat([source_df, edited_career], ignore_index=True)
        save_df(st.session_state.career_df, CAREER_FILE)
        st.success("진로 정보를 저장했습니다.")

    st.markdown("### 진로 통계")
    stat_df = st.session_state.career_df.copy()
    if not stat_df.empty:
        career_count = stat_df["희망진로"].value_counts().reset_index()
        career_count.columns = ["희망진로", "인원"]
        st.dataframe(career_count, use_container_width=True, hide_index=True)
    else:
        st.info("아직 저장된 진로 정보가 없습니다.")



def download_tab():
    st.subheader("4) 파일 다운로드")
    st.write("저장된 데이터를 CSV 파일로 내려받을 수 있습니다.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "학생 명단 다운로드",
            data=convert_df_to_csv(st.session_state.students_df),
            file_name="students.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "출석 데이터 다운로드",
            data=convert_df_to_csv(st.session_state.attendance_df),
            file_name="attendance.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "진로 데이터 다운로드",
            data=convert_df_to_csv(st.session_state.career_df),
            file_name="career.csv",
            mime="text/csv",
            use_container_width=True,
        )



def main():
    init_data()
    main_header()
    sidebar_controls()

    tab1, tab2, tab3, tab4 = st.tabs(["학생 명단", "출석 체크", "진로 체크", "다운로드"])

    with tab1:
        students_tab()
    with tab2:
        attendance_tab()
    with tab3:
        career_tab()
    with tab4:
        download_tab()


if __name__ == "__main__":
    main()
