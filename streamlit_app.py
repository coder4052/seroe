import streamlit as st
import pandas as pd
from collections import defaultdict
import re
from datetime import datetime, timezone, timedelta
import io
import plotly.express as px
import plotly.graph_objects as go
import json
import base64
import requests
from cryptography.fernet import Fernet
import gc
import time
import random
from datetime import datetime
import time

# ✅ product_mapping 모듈 import 추가
from product_mapping import get_product_info, get_mapping_stats

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

# GitHub 설정 - 수정된 저장소명
REPO_OWNER = "coder4052"  # 본인 GitHub 사용자명으로 변경하세요
REPO_NAME = "seroe"  # 실제 생성한 저장소명
SHIPMENT_FILE_PATH = "data/출고현황_encrypted.json"
BOX_FILE_PATH = "data/박스계산_encrypted.json"
STOCK_FILE_PATH = "data/재고현황_encrypted.json"

# ✅ 새로 추가: 컬럼 매핑 테이블
def detect_and_standardize_columns(df):
    """새로운 엑셀 양식의 컬럼명을 표준화"""
    rename_dict = {
        '노출상품명(옵션명)': '상품이름',
        '등록옵션명': '옵션이름',
        '구매수(수량)': '상품수량',
        '구매자': '주문자이름',
        '구매자전화번호': '주문자전화번호1'
    }
    
    detected = [f"{v} ← {k}" for k, v in rename_dict.items() if k in df.columns]
    if detected:
        st.success("✅ **새로운 엑셀 양식 감지!**")
        st.info("📋 **매핑**: " + " | ".join(detected))
    
    return df.rename(columns=rename_dict)



# 페이지 설정
st.set_page_config(
    page_title="서로 출고 현황",
    page_icon="🎯",
    layout="wide"
)

# 🎨 CSS 스타일 적용 - 가독성 향상
st.markdown("""
<style>
/* 전체 폰트 크기 및 가독성 향상 */
.main .block-container {
    font-size: 16px;
    line-height: 1.6;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 제목 스타일 */
h1 {
    font-size: 2.5rem !important;
    font-weight: bold !important;
    color: #1f1f1f !important;
    margin-bottom: 1rem !important;
}

/* 서브헤딩 스타일 */
h2 {
    font-size: 1.8rem !important;
    font-weight: 600 !important;
    color: #2c3e50 !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
}

h3 {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: #34495e !important;
    margin-top: 1.5rem !important;
    margin-bottom: 1rem !important;
}

/* 메트릭 카드 스타일 */
.metric-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* 데이터프레임 스타일 */
.dataframe {
    font-size: 14px !important;
    line-height: 1.5 !important;
}

/* 버튼 스타일 */
.stButton > button {
    font-size: 16px !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 8px !important;
}

/* 사이드바 스타일 */
.sidebar .sidebar-content {
    font-size: 15px !important;
    line-height: 1.6 !important;
}

/* 알림 메시지 스타일 */
.stAlert {
    font-size: 15px !important;
    font-weight: 500 !important;
    padding: 1rem !important;
    border-radius: 8px !important;
}

/* 테이블 헤더 스타일 */
.stDataFrame th {
    font-size: 15px !important;
    font-weight: 600 !important;
    background-color: #f8f9fa !important;
}

/* 테이블 셀 스타일 */
.stDataFrame td {
    font-size: 14px !important;
    padding: 0.75rem !important;
}

/* 확장기 스타일 */
.streamlit-expanderHeader {
    font-size: 16px !important;
    font-weight: 600 !important;
}

/* 캡션 스타일 */
.caption {
    font-size: 14px !important;
    color: #6c757d !important;
    font-style: italic !important;
}

/* 성공 메시지 스타일 */
.success-highlight {
    background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
    padding: 1rem;
    border-radius: 8px;
    color: white;
    font-weight: 600;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* 재고 부족 경고 스타일 (새로 추가) */
.low-stock-warning {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    color: white;
    padding: 1rem;
    border-radius: 8px;
    font-weight: bold;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* 재고 부족 테이블 행 스타일 (새로 추가) */
.stDataFrame [data-testid="stTable"] tbody tr td {
    font-weight: normal;
}

.low-stock-row {
    background-color: #ffebee !important;
    color: #c62828 !important;
    font-weight: bold !important;
}

/* 로딩 스피너 스타일 */
.loading-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 2rem;
}

/* 탭 버튼 크기 및 스타일 개선 */
.stTabs [data-baseweb="tab-list"] {
    gap: 15px !important;
    margin-bottom: 25px !important;
    padding: 10px 0 !important;
}

.stTabs [data-baseweb="tab-list"] button {
    font-size: 20px !important;
    font-weight: 700 !important;
    padding: 18px 30px !important;
    min-height: 60px !important;
    min-width: 150px !important;
    border-radius: 10px !important;
    margin-right: 0 !important;
    border: 2px solid #e0e0e0 !important;
    transition: all 0.2s ease !important;
    background-color: #ffffff !important;
    color: #666666 !important;
}

/* 탭 버튼 hover 효과 */
.stTabs [data-baseweb="tab-list"] button:hover {
    background-color: #f5f5f5 !important;
    color: #1f77b4 !important;
    border-color: #1f77b4 !important;
    transform: translateY(-1px) !important;
}

/* 활성 탭 스타일 */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    background-color: #1f77b4 !important;
    color: white !important;
    font-weight: 800 !important;
    border-color: #1f77b4 !important;
}
</style>
""", unsafe_allow_html=True)

# 새로운 박스 단순 규칙
BOX_RULES = {
    "박스 A": {"1L": (1, 2), "500ml": (1, 3), "240ml": (1, 5)},
    "박스 B": {"1L": (3, 4), "500ml": (4, 6), "240ml": (6, 10)},
    "박스 C": {"500ml": (10, 10)},
    "박스 D": {"1L": (5, 6)},
    "박스 E": {"1.5L": (3, 4)},
    "박스 F": {"1.5L": (1, 2)}
}

# 박스 비용 순서 (낮은 숫자가 더 저렴)
BOX_COST_ORDER = {
    "박스 A": 1,
    "박스 B": 2,
    "박스 C": 3,
    "박스 D": 4,
    "박스 E": 5,
    "박스 F": 6
}

# 🚨 재고 부족 임계값 설정 (새로 추가)
STOCK_THRESHOLDS = {
    "단호박식혜 1.5L": 10,
    "단호박식혜 1L": 20,
    "단호박식혜 240ml": 50,
    "식혜 1.5L": 20,
    "식혜 1L": 10,
    "식혜 240ml": 50,
    "수정과 500ml": 50,
    "플레인 쌀요거트 1L": 20,
    "플레인 쌀요거트 200ml": 10,
    "밥알없는 단호박식혜 1.5L": 1,
    "밥알없는 단호박식혜 1L": 1,
    "밥알없는 단호박식혜 240ml": 1,
    "밥알없는 식혜 1.5L": 1,
    "밥알없는 식혜 1L": 1,
    "밥알없는 식혜 240ml": 1,
}

# 🔒 보안 함수들
def sanitize_data(df):
    """민감정보 완전 제거 - 새로운 엑셀 양식 전용"""
    df = detect_and_standardize_columns(df)
    
    safe_columns = ['상품이름', '옵션이름', '상품수량', '수취인이름', '주문자이름', '주문자전화번호1']
    available_columns = df.columns.intersection(safe_columns)
    sanitized_df = df[available_columns].copy()
    
    essential_columns = ['상품이름', '옵션이름', '상품수량']
    missing_columns = [col for col in essential_columns if col not in sanitized_df.columns]
    if missing_columns:
        st.error(f"❌ 필수 컬럼이 없습니다: {missing_columns}")
        st.info("💡 새로운 엑셀 양식 컬럼을 확인하세요:")
        st.info("   - M열: 노출상품명(옵션명)")
        st.info("   - L열: 등록옵션명") 
        st.info("   - W열: 구매수(수량)")
        return pd.DataFrame()
    
    st.success(f"✅ 새로운 양식 처리 완료: {list(available_columns)}")
    return sanitized_df

def encrypt_results(results):
    """집계 결과 암호화"""
    try:
        key = st.secrets["encryption_key"]
        f = Fernet(key.encode())
        
        json_str = json.dumps(results, ensure_ascii=False)
        encrypted_data = f.encrypt(json_str.encode())
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        st.error(f"암호화 중 오류: {e}")
        return None

def decrypt_results(encrypted_data):
    """암호화된 결과 복호화"""
    try:
        key = st.secrets["encryption_key"]
        f = Fernet(key.encode())
        
        decoded_data = base64.b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded_data)
        return json.loads(decrypted_data.decode())
    except Exception as e:
        st.error(f"복호화 중 오류: {e}")
        return {}

def save_to_github(data, file_path, commit_message):
    """GitHub에 암호화된 데이터 저장 (공통 함수)"""
    try:
        github_token = st.secrets["github_token"]
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
        
        encrypted_data = encrypt_results(data)
        if not encrypted_data:
            return False
        
        data_package = {
            'encrypted_data': encrypted_data,
            'last_update': datetime.now(KST).isoformat(),
            'timestamp': datetime.now(KST).timestamp()
        }
        
        headers = {"Authorization": f"token {github_token}"}
        
        # 재시도 로직 추가
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                sha = response.json().get("sha") if response.status_code == 200 else None
                
                content = base64.b64encode(json.dumps(data_package, ensure_ascii=False, indent=2).encode()).decode()
                
                payload = {
                    "message": commit_message,
                    "content": content,
                    "branch": "main"
                }
                
                if sha:
                    payload["sha"] = sha
                
                response = requests.put(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code in [200, 201]:
                    return True
                else:
                    st.warning(f"GitHub 저장 실패 (시도 {attempt + 1}/{max_retries}): {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                st.warning(f"네트워크 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 지수 백오프
        
        return False
        
    except Exception as e:
        st.error(f"GitHub 저장 중 오류: {e}")
        return False

def load_from_github(file_path):
    """GitHub에서 암호화된 데이터 불러오기 (공통 함수) - 개선된 에러 처리"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            github_token = st.secrets["github_token"]
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
            
            headers = {"Authorization": f"token {github_token}"}
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                content = response.json()["content"]
                decoded_content = base64.b64decode(content).decode()
                data = json.loads(decoded_content)
                
                encrypted_results = data.get('encrypted_data')
                if encrypted_results:
                    results = decrypt_results(encrypted_results)
                    last_update_str = data.get('last_update')
                    last_update = datetime.fromisoformat(last_update_str) if last_update_str else None
                    return results, last_update
                    
            elif response.status_code == 404:
                # 파일이 없는 경우 - 정상적인 상황
                return {}, None
            else:
                # 다른 에러의 경우
                if attempt == max_retries - 1 and st.session_state.get('admin_mode', False):
                    st.warning(f"GitHub 데이터 로드 실패: {response.status_code}")
                    
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1 and st.session_state.get('admin_mode', False):
                st.warning(f"네트워크 오류로 인한 데이터 로드 실패: {str(e)}")
        except Exception as e:
            if attempt == max_retries - 1 and st.session_state.get('admin_mode', False):
                st.error(f"GitHub 데이터 로드 중 오류: {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(1)  # 재시도 전 대기
    
    return {}, None

def save_shipment_data(results):
    """출고 현황 데이터 저장"""
    commit_message = f"출고 현황 업데이트 - {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}"
    return save_to_github(results, SHIPMENT_FILE_PATH, commit_message)

def load_shipment_data():
    """출고 현황 데이터 불러오기"""
    return load_from_github(SHIPMENT_FILE_PATH)

def save_box_data(box_results):
    """박스 계산 데이터 저장"""
    commit_message = f"박스 계산 결과 업데이트 - {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}"
    return save_to_github(box_results, BOX_FILE_PATH, commit_message)

def load_box_data():
    """박스 계산 데이터 불러오기"""
    return load_from_github(BOX_FILE_PATH)

def save_stock_data(stock_results):
    """재고 현황 데이터 저장"""
    commit_message = f"재고 현황 업데이트 - {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}"
    return save_to_github(stock_results, STOCK_FILE_PATH, commit_message)

def load_stock_data():
    """재고 현황 데이터 불러오기"""
    return load_from_github(STOCK_FILE_PATH)

def get_stock_product_keys():
    """재고 관리용 상품 키 목록 생성 (출고 현황과 동기화)"""
    shipment_results, _ = load_shipment_data()
    if shipment_results:
        return sorted(shipment_results.keys())
    return []

def format_stock_display_time(datetime_str):
    """재고 입력 시간을 한국 시간대로 포맷팅"""
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        else:
            dt = dt.astimezone(KST)
        
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        weekday = weekdays[dt.weekday()]
        
        return dt.strftime(f"%m월 %d일 ({weekday}) %H:%M")
    except:
        return datetime_str

# 🔒 관리자 인증 함수
def check_admin_access():
    """관리자 권한 확인"""
    if "admin_mode" not in st.session_state:
        st.session_state.admin_mode = False
    
    if not st.session_state.admin_mode:
        st.sidebar.title("🔐 관리자 로그인")
        password = st.sidebar.text_input("관리자 비밀번호", type="password", key="admin_password")
        
        if st.sidebar.button("로그인"):
            try:
                if password == st.secrets["admin_password"]:
                    st.session_state.admin_mode = True
                    st.sidebar.success("✅ 관리자 로그인 성공!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ 비밀번호가 틀렸습니다")
            except Exception as e:
                st.sidebar.error("❌ 관리자 비밀번호 설정을 확인하세요")
        
        st.sidebar.markdown("""
        ### 👥 팀원 모드
        **이용 가능한 기능:**
        - 📊 최신 출고 현황 확인
        - 📦 택배박스 계산 결과 확인  
        - 📈 재고 현황 및 변동 확인
        - 📱 모바일에서도 확인 가능
        - 🔮 오늘의 운세
        
        **🔒 보안 정책:**
        - 고객 개인정보는 완전히 보호됩니다
        - 집계된 출고 현황만 표시됩니다
        """)
        
        return False
    else:
        st.sidebar.success("👑 관리자 모드 활성화")
        
        if st.sidebar.button("🚪 로그아웃"):
            st.session_state.admin_mode = False
            if "admin_password" in st.session_state:
                del st.session_state.admin_password
            st.rerun()
        
        return True

# 🔧 엑셀 파일 읽기 함수
def read_excel_file_safely(uploaded_file):
    """안전한 엑셀 파일 읽기 - 개선된 에러 처리"""
    df = None
    
    read_options = [
        {'engine': 'openpyxl', 'data_only': True},
        {'engine': 'openpyxl', 'data_only': False},
        {'engine': 'openpyxl'},
    ]
    
    for i, options in enumerate(read_options):
        try:
            # 파일 포인터 리셋
            uploaded_file.seek(0)
            
            # 실제 엑셀 파일 읽기
            df = pd.read_excel(uploaded_file, **options)
            
            if len(df) == 0:
                st.warning(f"⚠️ {uploaded_file.name}: 파일이 비어있습니다")
                continue
                
            if i == 0:
                st.success(f"✅ {uploaded_file.name}: 최적화된 방식으로 읽기 성공")
            else:
                st.info(f"ℹ️ {uploaded_file.name}: 대체 방식으로 읽기 성공")
            break
            
        except Exception as e:
            if i == len(read_options) - 1:
                st.error(f"❌ {uploaded_file.name}: 모든 읽기 방식 실패")
                st.error(f"오류 상세: {str(e)}")
                st.info("💡 파일이 손상되었거나 올바른 Excel 형식이 아닐 수 있습니다.")
            continue
    
    return df

# ✅ 새로운 용량 표준화 함수들 (용도별 분리)
def standardize_capacity_for_display(capacity):
    """용량 표준화 - 출고 현황/재고 관리용 (200ml 그대로 표시)"""
    if not capacity:
        return ""
    
    capacity = str(capacity)
    
    if re.match(r'1\.5L', capacity, re.IGNORECASE):
        return "1.5L"
    if re.match(r'1L|1000ml', capacity, re.IGNORECASE):
        return "1L"
    if re.match(r'500ml', capacity, re.IGNORECASE):
        return "500ml"
    if re.match(r'240ml', capacity, re.IGNORECASE):
        return "240ml"
    if re.match(r'200ml', capacity, re.IGNORECASE):
        return "200ml"  # 200ml 그대로 유지
    
    return capacity

def standardize_capacity_for_box(capacity):
    """용량 표준화 - 박스 계산용 (200ml → 240ml 변환)"""
    if not capacity:
        return ""
    
    capacity = str(capacity)
    
    if re.match(r'1\.5L', capacity, re.IGNORECASE):
        return "1.5L"
    if re.match(r'1L|1000ml', capacity, re.IGNORECASE):
        return "1L"
    if re.match(r'500ml', capacity, re.IGNORECASE):
        return "500ml"
    if re.match(r'240ml', capacity, re.IGNORECASE):
        return "240ml"
    if re.match(r'200ml', capacity, re.IGNORECASE):
        return "240ml"  # 200ml → 240ml 변환
    
    return capacity

# 📦 박스 계산 함수들 (완전히 새로운 방식)
def group_orders_by_recipient_new(df):
    """수취인별로 주문을 그룹화하여 박스 계산 - 새로운 매핑 방식"""
    orders = defaultdict(dict)
    
    for _, row in df.iterrows():
        # 복합 키 생성: 수취인이름 + 주문자이름으로 동명이인 구분
        recipient_name = row.get('수취인이름', '알 수 없음')
        orderer_name = row.get('주문자이름', '').strip()

        # 고유 식별자 생성
        if orderer_name and orderer_name != recipient_name:
            recipient_key = f"{recipient_name} - 주문자: {orderer_name}"
        else:
            recipient_key = f"{recipient_name} - 직접주문"
        
        # ✅ 새로운 매핑 방식 사용
        product_type, capacity, option_count = get_product_info(
            row.get('상품이름', ''), 
            row.get('옵션이름', '')
        )
        
        try:
            base_quantity = int(row.get('상품수량', 1))
        except (ValueError, TypeError):
            base_quantity = 1
        
        total_quantity = base_quantity * option_count
        
        # 박스 계산용 용량 표준화 (200ml → 240ml)
        standardized_capacity = standardize_capacity_for_box(capacity)
        
        if standardized_capacity:
            key = f"{product_type} {standardized_capacity}"
        else:
            key = product_type
        
        orders[recipient_key][key] = orders[recipient_key].get(key, 0) + total_quantity
    
    return orders

def get_product_quantities(order_products):
    """주문 제품에서 용량별 수량 집계 - 새로운 규칙"""
    quantities = defaultdict(int)
    
    for product_key, qty in order_products.items():
        if '1.5L' in product_key:
            quantities['1.5L'] += qty
        elif '1L' in product_key:
            quantities['1L'] += qty
        elif '500ml' in product_key:
            quantities['500ml'] += qty
        elif '240ml' in product_key:
            quantities['240ml'] += qty
        elif '200ml' in product_key:
            quantities['240ml'] += qty  # 200ml → 240ml 변환
    
    return quantities

def calculate_box_for_order(quantities):
    """단일 주문에 대한 박스 계산 - 새로운 간단 규칙"""
    
    # 1단계: 혼합 주문 체크 (여러 용량이 섞여있으면 검토 필요)
    non_zero_capacities = [cap for cap, qty in quantities.items() if qty > 0]
    if len(non_zero_capacities) > 1:
        return "검토 필요"
    
    # 2단계: 단일 용량 박스 매칭
    for capacity, qty in quantities.items():
        if qty > 0:
            # 박스 A: 1L 1~2개 or 500ml 1~3개 or 240ml 1~5개
            if capacity == "1L" and 1 <= qty <= 2:
                return "박스 A"
            elif capacity == "500ml" and 1 <= qty <= 3:
                return "박스 A"
            elif capacity == "240ml" and 1 <= qty <= 5:
                return "박스 A"
            
            # 박스 B: 1L 3~4개 or 500ml 4~6개 or 240ml 6~10개
            elif capacity == "1L" and 3 <= qty <= 4:
                return "박스 B"
            elif capacity == "500ml" and 4 <= qty <= 6:
                return "박스 B"
            elif capacity == "240ml" and 6 <= qty <= 10:
                return "박스 B"
            
            # 박스 C: 500ml 10개
            elif capacity == "500ml" and qty == 10:
                return "박스 C"
            
            # 박스 D: 1L 5~6개
            elif capacity == "1L" and 5 <= qty <= 6:
                return "박스 D"
            
            # 박스 E: 1.5L 3~4개
            elif capacity == "1.5L" and 3 <= qty <= 4:
                return "박스 E"
            
            # 박스 F: 1.5L 1~2개
            elif capacity == "1.5L" and 1 <= qty <= 2:
                return "박스 F"
    
    # 3단계: 어떤 박스 조건도 만족하지 않으면 검토 필요
    return "검토 필요"

def calculate_box_requirements_new(df):
    """전체 박스 필요량 계산 - 새로운 매핑 로직"""
    orders = group_orders_by_recipient_new(df)
    
    total_boxes = defaultdict(int)
    review_orders = []  # 검토 필요 주문들
    
    for recipient, products in orders.items():
        quantities = get_product_quantities(products)
        box_result = calculate_box_for_order(quantities)
        
        if box_result == "검토 필요":
            review_orders.append({
                'recipient': recipient,
                'quantities': quantities,
                'products': products
            })
        else:
            total_boxes[box_result] += 1
    
    return total_boxes, review_orders

def process_unified_file_new(uploaded_file):
    """통합 엑셀 파일 처리 - 새로운 매핑 방식 (개선된 메모리 관리)"""
    try:
        df = read_excel_file_safely(uploaded_file)
        
        if df is None:
            return {}, [], {}
        
        df = sanitize_data(df)
        
        if df.empty:
            return {}, [], {}
        
        st.write(f"📄 **{uploaded_file.name}**: 통합 파일 처리 시작 (총 {len(df):,}개 주문)")
        
        results = defaultdict(int)
        mapping_failures = []  # 매핑 실패 케이스 추적
        
        # 프로그레스 바 추가
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_rows = len(df)
        
        for index, row in df.iterrows():
            # 프로그레스 업데이트
            progress = (index + 1) / total_rows
            progress_bar.progress(progress)
            status_text.text(f"처리 중... {index + 1:,}/{total_rows:,} ({progress:.1%})")
            
            # ✅ 새로운 매핑 방식 사용
            product_type, capacity, option_count = get_product_info(
                row.get('상품이름', ''), 
                row.get('옵션이름', '')
            )
            
            # 매핑 실패 케이스 기록
            if product_type == "기타":
                mapping_failures.append({
                    'row': index + 1,
                    'product_name': row.get('상품이름', ''),
                    'option_name': row.get('옵션이름', ''),
                    'quantity': row.get('상품수량', 1)
                })
            
            try:
                base_quantity = int(row.get('상품수량', 1))
            except (ValueError, TypeError):
                base_quantity = 1
                
            total_quantity = base_quantity * option_count
            
            # 출고 현황용 용량 표준화 (200ml 그대로)
            standardized_capacity = standardize_capacity_for_display(capacity)
            
            if standardized_capacity:
                key = f"{product_type} {standardized_capacity}"
            else:
                key = product_type
            
            results[key] += total_quantity
        
        # 프로그레스 바 정리
        progress_bar.empty()
        status_text.empty()
        
        processed_files = [f"통합 파일 ({len(df):,}개 주문)"]
        
        # 매핑 실패 통계
        mapping_stats = {
            'total_processed': len(df),
            'successful_mappings': len(df) - len(mapping_failures),
            'failed_mappings': len(mapping_failures),
            'success_rate': ((len(df) - len(mapping_failures)) / len(df) * 100) if len(df) > 0 else 0,
            'failure_details': mapping_failures
        }
        
        # 메모리 정리 추가
        del df
        gc.collect()
        
        return results, processed_files, mapping_stats
        
    except Exception as e:
        st.error(f"❌ {uploaded_file.name} 처리 중 오류: {str(e)}")
        return {}, [], {}

def get_product_color(product_name):
    """상품명에 따른 색상 반환"""
    if "단호박식혜" in product_name:
        return "#FFD700"  # 황금색
    elif "수정과" in product_name:
        return "#D2B48C"  # 갈색
    elif "식혜" in product_name and "단호박" not in product_name:
        return "#654321"  # 갈색
    elif "플레인" in product_name or "쌀요거트" in product_name:
        return "#F5F5F5"  # 밝은 회색
    else:
        return "#808080"  # 회색

# 한국 시간 기준 날짜 정보 생성
def get_korean_date():
    """한국 시간 기준 날짜 정보 반환"""
    now = datetime.now(KST)
    weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    weekday = weekdays[now.weekday()]
    
    return now.strftime(f"%Y년 %m월 %d일 ({weekday})")

# 메인 페이지 - 영구 저장 시스템
korean_date = get_korean_date()
st.title(f"🎯 서로별 관리 시스템 - {korean_date}")
st.markdown("### 🔒 보안 강화 버전")

# ✅ 매핑 모듈 정보 표시 (관리자 모드에서만)
if st.session_state.get('admin_mode', False):
    try:
        mapping_stats = get_mapping_stats()
        st.sidebar.success(f"🎯 매핑 모듈: {mapping_stats['total_cases']}개 케이스 로드됨")
    except:
        st.sidebar.warning("⚠️ 매핑 모듈 로드 실패")

# 관리자 권한 확인
is_admin = check_admin_access()

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📦 출고 현황", "📦 박스 계산", "📊 재고 관리"])

# 첫 번째 탭: 출고 현황
with tab1:
    st.header("📦 출고 현황")
    
    # 출고 현황 데이터 로드
    with st.spinner('📡 출고 현황 데이터 로드 중...'):
        shipment_results, shipment_last_update = load_shipment_data()
    
    if shipment_results:
        # 출고 현황 계산
        total_quantity = sum(shipment_results.values())
        product_types = len([k for k, v in shipment_results.items() if v > 0])
        
        # 요약 메트릭 표시 - 개선된 버전
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 24px; color: white; margin-bottom: 10px; font-weight: 600;">
                        🎯 전체 출고 개수
                    </div>
                    <div style="font-size: 42px; font-weight: bold; color: white;">
                        {total_quantity:,}개
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%); 
                            border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 24px; color: white; margin-bottom: 10px; font-weight: 600;">
                        📊 상품 종류
                    </div>
                    <div style="font-size: 42px; font-weight: bold; color: white;">
                        {product_types}개
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # 업데이트 시간 표시
        if shipment_last_update:
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                        padding: 15px; border-radius: 10px; margin: 20px 0; 
                        border-left: 4px solid #667eea; text-align: center;">
                <div style="font-size: 18px; color: #2c3e50; font-weight: 600;">
                    📅 마지막 업데이트: {shipment_last_update.strftime('%Y년 %m월 %d일 %H시 %M분')} (KST)
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # 출고 현황 테이블 데이터 준비
        df_data = []
        for product_key, quantity in sorted(shipment_results.items()):
            if quantity > 0:
                parts = product_key.strip().split()
                if len(parts) >= 2:
                    last_part = parts[-1]
                    if re.match(r'\d+(?:\.\d+)?(?:ml|L)', last_part):
                        product_name = ' '.join(parts[:-1])
                        capacity = last_part
                    else:
                        product_name = product_key
                        capacity = ""
                else:
                    product_name = product_key
                    capacity = ""
                
                df_data.append({
                    "상품명": product_name,
                    "용량": capacity,
                    "수량": quantity
                })
        
        if df_data:
            df_display = pd.DataFrame(df_data)
            
            # 상품별 출고 현황 - 카드 형태로 표시
            st.markdown("#### 📦 상품별 출고 현황")
            
            for i, row in df_display.iterrows():
                # 상품명에 따라 배경색 결정
                product_name = row["상품명"]
                
                if "단호박식혜" in product_name:
                    # 노란색 계열
                    background_color = "linear-gradient(135deg, #ffd700 0%, #ffb300 100%)"
                    text_color = "#4a4a4a"  # 어두운 회색 (노란색 배경에 잘 보이도록)
                elif "수정과" in product_name:
                    # 진갈색 계열
                    background_color = "linear-gradient(135deg, #8b4513 0%, #654321 100%)"
                    text_color = "#ffffff"  # 흰색
                elif "식혜" in product_name and "단호박" not in product_name:
                    # 연갈색 계열
                    background_color = "linear-gradient(135deg, #d2b48c 0%, #bc9a6a 100%)"
                    text_color = "#4a4a4a"  # 어두운 회색 (연갈색 배경에 잘 보이도록)
                elif "플레인" in product_name or "쌀요거트" in product_name:
                    # 검정색 계열
                    background_color = "linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%)"
                    text_color = "#ffffff"  # 흰색
                else:
                    # 기본 초록색 (기타 상품)
                    background_color = "linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)"
                    text_color = "#ffffff"  # 흰색
                
                st.markdown(f"""
                    <div style="background: {background_color}; 
                                color: {text_color}; padding: 25px; border-radius: 20px; 
                                margin: 15px 0; box-shadow: 0 6px 12px rgba(0,0,0,0.15);">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div>
                                <span style="font-size: 28px; font-weight: bold; color: {text_color};">{row["상품명"]}</span>
                                <br>
                                <span style="font-size: 24px; font-weight: normal; opacity: 0.85; color: {text_color};">
                                    ({row["용량"]})
                                </span>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-size: 32px; font-weight: bold; color: {text_color};">
                                    {row["수량"]}개
                                </span>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("📊 **아직 업데이트된 출고 현황이 없습니다. 관리자가 데이터를 업로드할 때까지 기다려주세요.**")

# 두 번째 탭: 박스 계산
with tab2:
    st.header("📦 박스 개수 계산 결과")
    
    # 박스 계산 데이터 로드
    with st.spinner('📡 박스 계산 데이터 로드 중...'):
        box_data, box_last_update = load_box_data()
    
    if box_data:
        total_boxes = box_data.get('total_boxes', {})
        box_e_orders = box_data.get('box_e_orders', [])
        
        # 박스 요약 메트릭
        total_box_count = sum(total_boxes.values())
        box_e_count = len(box_e_orders)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 24px; color: white; margin-bottom: 10px; font-weight: 600;">
                        📦 총 박스 개수
                    </div>
                    <div style="font-size: 42px; font-weight: bold; color: white;">
                        {total_box_count}개
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            color = "#f44336" if box_e_count > 0 else "#4caf50"
            st.markdown(f"""
                <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, {color} 0%, {'#d32f2f' if box_e_count > 0 else '#388e3c'} 100%); 
                            border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <div style="font-size: 24px; color: white; margin-bottom: 10px; font-weight: 600;">
                        ⚠️ 박스 검토
                    </div>
                    <div style="font-size: 42px; font-weight: bold; color: white;">
                        {box_e_count}개
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # 업데이트 시간 표시
        if box_last_update:
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                        padding: 15px; border-radius: 10px; margin: 20px 0; 
                        border-left: 4px solid #667eea; text-align: center;">
                <div style="font-size: 18px; color: #2c3e50; font-weight: 600;">
                    📅 마지막 업데이트: {box_last_update.strftime('%Y년 %m월 %d일 %H시 %M분')} (KST)
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # 일반 박스 계산
        sorted_boxes = sorted(total_boxes.items(), key=lambda x: BOX_COST_ORDER.get(x[0], 999))

        # 박스 설명
        BOX_DESCRIPTIONS = {
            "박스 A": "1L 1~2개, 500ml 1~3개, 240ml 1~5개",
            "박스 B": "1L 3~4개, 500ml 4~6개, 240ml 6~10개", 
            "박스 C": "500ml 10개",
            "박스 D": "1L 5~6개",
            "박스 E": "1.5L 3~4개",
            "박스 F": "1.5L 1~2개"
        }
        
        st.markdown("#### 📦 박스별 필요량")
        
        # 박스별 필요량을 개선된 형태로 표시
        for box_name, count in sorted_boxes:
            if box_name != '박스 E':
                description = BOX_DESCRIPTIONS.get(box_name, "")
                
                # 박스 A, B의 경우 용량 글자 크기를 조금 줄임
                description_font_size = "14px" if box_name in ["박스 A", "박스 B"] else "16px"
                
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%); 
                                color: white; padding: 25px; border-radius: 20px; 
                                margin: 15px 0; box-shadow: 0 6px 12px rgba(0,0,0,0.15);">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div>
                                <span style="font-size: 28px; font-weight: bold; color: #ffffff;">{box_name}</span>
                                <br>
                                <span style="font-size: {description_font_size}; font-weight: normal; opacity: 0.85; color: #e8f5e8;">
                                    ({description})
                                </span>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-size: 32px; font-weight: bold; color: #ffffff;">
                                    {count}개
                                </span>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        # 검토 필요 주문 표시
        if box_e_count > 0:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); 
                            color: white; padding: 25px; border-radius: 20px; 
                            margin: 15px 0; box-shadow: 0 6px 12px rgba(0,0,0,0.15);">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <span style="font-size: 28px; font-weight: bold; color: #ffffff;">검토 필요 주문</span>
                            <br>
                            <span style="font-size: 16px; font-weight: normal; opacity: 0.85; color: #ffe8e8;">
                                (수동 검토가 필요한 주문)
                            </span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 32px; font-weight: bold; color: #ffffff;">
                                {box_e_count}개
                            </span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
                
        # 박스 검토 필요 주문 (있을 경우에만)
        if box_e_orders:
            st.markdown("### ⚠️ 박스 검토 필요 주문")
            st.warning(f"📋 **총 {len(box_e_orders)}건의 주문이 박스 검토가 필요합니다.**")
            
            # 간단한 요약 테이블 - 주문 내역 중심
            summary_data = []
            for i, order in enumerate(box_e_orders, 1):
                quantities = order.get('quantities', {})
                
                # 주문 내역 문자열 생성
                order_details = []
                for capacity in ['1.5L', '1L', '500ml', '240ml']:
                    qty = quantities.get(capacity, 0)
                    if qty > 0:
                        order_details.append(f"{capacity} {qty}개")
                
                summary_data.append({
                    "검토 대상": f"#{i}",
                    "주문 내역": ", ".join(order_details) if order_details else "확인 필요"
                })
            
            if summary_data:
                st.markdown("#### 📋 박스 검토 주문 요약")
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
        else:
            st.success("✅ **모든 주문이 일반 박스(A~D, F)로 처리 가능합니다!**")
    
    else:
        st.info("📦 **박스 계산 데이터를 확인하려면 관리자가 수취인이름이 포함된 통합 엑셀 파일을 업로드해야 합니다.**")

# 세 번째 탭: 재고 관리 (기존 코드와 동일하므로 유지)
with tab3:
    st.header("📊 재고 관리")
    
    # 재고 데이터 로드
    with st.spinner('📡 재고 데이터 로드 중...'):
        stock_results, stock_last_update = load_stock_data()
    
    # 한국 시간 기준 날짜 정보
    today = datetime.now(KST)
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday = weekdays[today.weekday()]
    today_date_label = today.strftime(f"%m월 %d일 ({weekday})")
    
    # 전체 상품 목록 (항상 표시될 모든 제품) - 출고 현황과 관계없이
    ALL_PRODUCTS = [
        "단호박식혜 1.5L",
        "단호박식혜 1L",
        "단호박식혜 240ml",
        "식혜 1.5L",
        "식혜 1L",
        "식혜 240ml",
        "수정과 500ml",
        "밥알없는 단호박식혜 1.5L",
        "밥알없는 단호박식혜 1L",
        "밥알없는 단호박식혜 240ml",
        "밥알없는 식혜 1.5L",
        "밥알없는 식혜 1L",
        "밥알없는 식혜 240ml",
        "플레인 쌀요거트 1L",
        "플레인 쌀요거트 200ml"
    ]
    
    # 모든 상품을 기본으로 설정
    product_keys = set(ALL_PRODUCTS)
    
    # 출고 현황에 있는 추가 상품들도 포함 (혹시 누락된 것들을 위해)
    shipment_results, _ = load_shipment_data()
    if shipment_results:
        product_keys.update(shipment_results.keys())
    
    product_keys = sorted(list(product_keys))
    
    if product_keys:
        st.info(f"📋 **{today_date_label} 재고 입력** - 상품/용량별로 현재 재고 수량을 입력하세요")

        # 출고 현황 반영 버튼 추가
        if shipment_results:
            st.markdown("### 📦 출고 현황 반영")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info("💡 **출고 현황 반영**: 현재 재고에서 출고된 수량을 자동으로 차감하여 실제 재고량을 계산합니다.")
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📦 출고 현황 반영", help="출고된 수량만큼 재고를 자동으로 차감합니다"):
                    # 현재 재고 이력 로드
                    current_stock = stock_results if stock_results else {}
                    
                    # 최신 재고 입력 가져오기
                    latest_stock = {}
                    if current_stock.get("최근입력"):
                        latest_stock = current_stock["최근입력"]["입력용"].copy()
                    
                    # 출고 현황 적용
                    updated_stock = {}
                    for product_key in product_keys:
                        # 상품명과 용량 분리
                        parts = product_key.strip().split()
                        if len(parts) >= 2 and re.match(r'\d+(?:\.\d+)?(?:ml|L)', parts[-1]):
                            product_name = ' '.join(parts[:-1])
                            capacity = parts[-1]
                        else:
                            product_name = product_key
                            capacity = ""
                        
                        input_key = f"{product_name}|{capacity}"
                        
                        # 현재 재고량
                        current_qty = latest_stock.get(input_key, 0)
                        
                        # 출고량 (shipment_results에서 찾기)
                        shipment_qty = shipment_results.get(product_key, 0)
                        
                        # 차감 계산 (0 이하로 내려가지 않게)
                        final_qty = max(0, current_qty - shipment_qty)
                        updated_stock[input_key] = final_qty
                    
                    # 새로운 입력 이력 생성
                    now_str = today.strftime("%Y-%m-%d %H:%M:%S")
                    new_entry = {
                        "입력일시": now_str,
                        "입력용": updated_stock.copy(),
                        "출고반영": True  # 출고 반영 표시
                    }
                    
                    # 이력 업데이트
                    if "이력" not in current_stock:
                        current_stock["이력"] = []
                    
                    # 최신 입력을 맨 앞에 추가
                    current_stock["이력"].insert(0, new_entry)
                    current_stock["최근입력"] = new_entry
                    
                    # GitHub에 저장
                    commit_message = f"출고 현황 반영 {today_date_label} {today.strftime('%H:%M')}"
                    save_success = save_stock_data(current_stock)
                    
                    if save_success:
                        st.success("✅ 출고 현황이 재고에 성공적으로 반영되었습니다!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 출고 현황 반영 중 오류가 발생했습니다. 다시 시도해주세요.")

        # 먼저 재고 현황 표시
        if stock_results and stock_results.get("최근입력"):
            latest_entry = stock_results["최근입력"]
            input_time = latest_entry["입력일시"]

            # 시간 포맷팅
            try:
                dt = datetime.fromisoformat(input_time.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=KST)
                else:
                    dt = dt.astimezone(KST)
                
                formatted_time = dt.strftime("%Y-%m-%d-%H-%M")
            except:
                formatted_time = input_time.replace(" ", "-").replace(":", "-")

            # 출고 반영 여부 표시
            reflection_type = "출고 반영" if latest_entry.get("출고반영", False) else "수동 입력"

            st.markdown(f"### 📋 재고 현황 ({formatted_time}) - {reflection_type}")

            # 현재 재고 데이터를 상품별로 그룹화
            stock_groups = {}
            low_stock_items = []

            for product_key, quantity in latest_entry["입력용"].items():
                if quantity > 0:  # 수량이 0보다 큰 경우만 표시
                    product_name, capacity = product_key.split("|", 1)
                    full_product_name = f"{product_name} {capacity}".strip()
                    
                    # 임계값 확인 (표시하지 않고 색상 결정용)
                    threshold = STOCK_THRESHOLDS.get(full_product_name, 0)
                    is_low_stock = quantity <= threshold and threshold > 0
                    
                    if is_low_stock:
                        low_stock_items.append(f"{full_product_name} ({quantity}개)")
                    
                    if product_name not in stock_groups:
                        stock_groups[product_name] = []
                    
                    stock_groups[product_name].append({
                        "용량": capacity,
                        "수량": quantity,
                        "위험": is_low_stock
                    })

            # 상품별 카드 형태로 재고 현황 표시
            for product_name, capacities in stock_groups.items():
                # 상품명에 따라 색상 결정 (출고 현황 탭과 동일한 로직)
                if "밥알없는 단호박식혜" in product_name:
                    # 밥알없는 단호박식혜 - 진한 노란색
                    card_color = "linear-gradient(135deg, #ffb300 0%, #ff8f00 100%)"
                    border_color = "#ff6f00"
                    text_color = "#4a4a4a"
                elif "단호박식혜" in product_name:
                    # 일반 단호박식혜 - 기본 노란색
                    card_color = "linear-gradient(135deg, #ffd700 0%, #ffb300 100%)"
                    border_color = "#ff8f00"
                    text_color = "#4a4a4a"
                elif "밥알없는 식혜" in product_name:
                    # 밥알없는 식혜 - 연한 갈색
                    card_color = "linear-gradient(135deg, #deb887 0%, #d2b48c 100%)"
                    border_color = "#cd853f"
                    text_color = "#4a4a4a"
                elif "식혜" in product_name and "단호박" not in product_name:
                    # 일반 식혜 - 기본 갈색
                    card_color = "linear-gradient(135deg, #d2b48c 0%, #bc9a6a 100%)"
                    border_color = "#8b7355"
                    text_color = "#4a4a4a"
                elif "수정과" in product_name:
                    # 수정과 - 진갈색
                    card_color = "linear-gradient(135deg, #8b4513 0%, #654321 100%)"
                    border_color = "#654321"
                    text_color = "#ffffff"
                elif "플레인" in product_name or "쌀요거트" in product_name:
                    # 플레인 쌀요거트 - 검정색
                    card_color = "linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%)"
                    border_color = "#000000"
                    text_color = "#ffffff"
                else:
                    # 기타 상품 - 기본 초록색
                    card_color = "linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%)"
                    border_color = "#4caf50"
                    text_color = "#2e7d32"
                
                st.markdown(f"""
                    <div style="background: {card_color}; 
                                padding: 20px; border-radius: 15px; margin: 15px 0; 
                                border-left: 5px solid {border_color};">
                        <h4 style="margin: 0 0 15px 0; color: {text_color}; font-weight: 600;">
                            📦 {product_name}
                        </h4>
                    </div>
                """, unsafe_allow_html=True)
                
                # 해당 상품의 용량별 재고를 한 줄에 표시
                cols = st.columns(len(capacities))
                
                for i, item in enumerate(capacities):
                    with cols[i]:
                        # 각 용량별로 개별적으로 색상 결정
                        if item["위험"]:
                            # 임계치 이하인 용량만 빨간색
                            st.markdown(f"""
                                <div style="text-align: center; padding: 10px; 
                                            background: white; border-radius: 8px; 
                                            border: 2px solid #f44336;">
                                    <div style="font-size: 18px; color: #666; margin-bottom: 5px;">
                                        {item["용량"]}
                                    </div>
                                    <div style="font-size: 24px; font-weight: bold; color: #f44336;">
                                        {item["수량"]}개
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            # 정상 재고는 초록색
                            st.markdown(f"""
                                <div style="text-align: center; padding: 10px; 
                                            background: white; border-radius: 8px; 
                                            border: 2px solid #4caf50;">
                                    <div style="font-size: 18px; color: #666; margin-bottom: 5px;">
                                        {item["용량"]}
                                    </div>
                                    <div style="font-size: 24px; font-weight: bold; color: #4caf50;">
                                        {item["수량"]}개
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                                
            # 재고 요약 정보
            total_products = sum(len(capacities) for capacities in stock_groups.values())
            total_quantity = sum(sum(item["수량"] for item in capacities) for capacities in stock_groups.values())
            low_stock_count = len(low_stock_items)

            # 여백 추가 (거리 넓히기)
            st.markdown("<br><br>", unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: white; border-radius: 10px; border: 2px solid #e9ecef;">
                        <div style="font-size: 20px; color: #666; margin-bottom: 10px; font-weight: 600;">
                            📊 재고 상품 종류
                        </div>
                        <div style="font-size: 32px; font-weight: bold; color: #2c3e50;">
                            {total_products}개
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: white; border-radius: 10px; border: 2px solid #e9ecef;">
                        <div style="font-size: 20px; color: #666; margin-bottom: 10px; font-weight: 600;">
                            📦 총 재고 수량
                        </div>
                        <div style="font-size: 32px; font-weight: bold; color: #2c3e50;">
                            {total_quantity:,}개
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # 재고 부족 항목의 경우 빨간색으로 표시
                color = "#f44336" if low_stock_count > 0 else "#2c3e50"
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: white; border-radius: 10px; border: 2px solid #e9ecef;">
                        <div style="font-size: 20px; color: #666; margin-bottom: 10px; font-weight: 600;">
                            🚨 재고 부족 항목
                        </div>
                        <div style="font-size: 32px; font-weight: bold; color: {color};">
                            {low_stock_count}개
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br><br>", unsafe_allow_html=True)
            
            st.markdown(f'📅 마지막 업데이트: {dt.strftime("%Y년 %m월 %d일 %H시 %M분")} (KST)')
            
            # 재고가 없는 경우 메시지 표시
            if not stock_groups:
                st.info("📋 **현재 재고가 있는 상품이 없습니다.**")
        else:
            st.info("📋 **재고 데이터가 없습니다. 재고를 처음 입력하시면 현황이 표시됩니다.**")

        # 구분선 추가
        st.markdown("---")
        
        # 재고 입력 폼
        with st.form(f"stock_input_{today.strftime('%Y%m%d')}"):
            st.markdown("#### 💾 재고 수량 입력")
            st.markdown("상품/용량별로 현재 남은 재고 개수를 입력하세요")
            
            stock_input = {}
            
            # 상품별로 그룹화
            product_groups = {}
            for product_key in product_keys:
                parts = product_key.strip().split()
                if len(parts) >= 2 and re.match(r'\d+(?:\.\d+)?(?:ml|L)', parts[-1]):
                    product_name = ' '.join(parts[:-1])
                    capacity = parts[-1]
                else:
                    product_name = product_key
                    capacity = ""
                
                if product_name not in product_groups:
                    product_groups[product_name] = []
                product_groups[product_name].append((capacity, product_key))
            
            # 상품별 입력 필드 생성
            for product_name, capacities in sorted(product_groups.items()):
                st.markdown(f"**📦 {product_name}**")
                
                # 용량별로 컬럼 생성
                if len(capacities) > 1:
                    cols = st.columns(len(capacities))
                    for i, (capacity, product_key) in enumerate(capacities):
                        with cols[i]:
                            # 기존 재고 값 가져오기 (있다면)
                            existing_value = 0
                            if stock_results and stock_results.get("최근입력"):
                                input_key = f"{product_name}|{capacity}"
                                existing_value = stock_results["최근입력"]["입력용"].get(input_key, 0)
                            
                            label_text = f"{capacity}" if capacity else "기본 용량"
                            stock_input[f"{product_name}|{capacity}"] = st.number_input(
                                label_text,
                                min_value=0,
                                value=existing_value,
                                step=1,
                                key=f"stock_{product_name}_{capacity}"
                            )
                else:
                    # 단일 용량인 경우
                    capacity, product_key = capacities[0]
                    
                    # 기존 재고 값 가져오기 (있다면)
                    existing_value = 0
                    if stock_results and stock_results.get("최근입력"):
                        input_key = f"{product_name}|{capacity}"
                        existing_value = stock_results["최근입력"]["입력용"].get(input_key, 0)
                    
                    label_text = f"{capacity}" if capacity else "기본 용량"  
                    stock_input[f"{product_name}|{capacity}"] = st.number_input(
                        label_text,
                        min_value=0,
                        value=existing_value,
                        step=1,
                        key=f"stock_{product_name}_{capacity}"
                    )            
            # 저장 버튼
            submitted = st.form_submit_button("💾 재고 저장", help="입력한 재고 수량을 저장합니다")
            
            if submitted:
                # 현재 재고 이력 로드
                current_stock = stock_results if stock_results else {}
                
                # 새로운 입력 이력 생성
                now_str = today.strftime("%Y-%m-%d %H:%M:%S")
                new_entry = {
                    "입력일시": now_str,
                    "입력용": stock_input.copy(),
                    "출고반영": False  # 수동 입력 표시
                }
                
                # 이력 업데이트
                if "이력" not in current_stock:
                    current_stock["이력"] = []
                
                # 최신 입력을 맨 앞에 추가
                current_stock["이력"].insert(0, new_entry)
                current_stock["최근입력"] = new_entry
                
                # GitHub에 저장
                commit_message = f"재고 입력 {today_date_label} {today.strftime('%H:%M')}"
                save_success = save_stock_data(current_stock)
                
                if save_success:
                    st.success("✅ 재고 입력이 성공적으로 저장되었습니다!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 재고 저장 중 오류가 발생했습니다. 다시 시도해주세요.")

    else:
        st.info("📋 **재고 관리를 위해서는 먼저 출고 현황 데이터가 필요합니다.**")
        st.markdown("관리자가 출고 현황을 업로드하면 자동으로 재고 입력이 가능해집니다.")

# 관리자 파일 업로드 (새로운 매핑 방식)
if is_admin:
    st.markdown("---")
    st.markdown("## 👑 관리자 전용 - 통합 파일 업로드")
    
    st.info("""
    🔒 **보안 정책**: 업로드된 엑셀 파일의 고객 개인정보는 즉시 제거되며, 집계 결과만 암호화되어 저장됩니다.
    
    📝 **영구 저장 시스템**:
    - 출고 현황, 박스 계산, 재고 관리 결과가 모두 GitHub에 암호화되어 저장됩니다
    - 로그아웃, 새로고침, 탭 닫기와 무관하게 지속적으로 표시됩니다
    - 모든 팀원이 언제든지 최신 결과를 확인할 수 있습니다
    - **출고 현황**: 200ml 그대로 표시
    - **박스 계산**: 200ml을 240ml과 동일하게 처리
    - **재고 관리**: 출고 현황과 자동 동기화
    - **.xlsx 형식만 지원**
    
    ✅ **새로운 기능**: 94개 케이스 완전 매핑 + 기타 제품 추적
    """)
    
    uploaded_file = st.file_uploader(
        "📁 통합 엑셀 파일을 업로드하세요 (.xlsx만 지원)",
        type=['xlsx'],
        help="통합 출고내역서(.xlsx)를 업로드하세요. 고객 정보는 자동으로 제거됩니다.",
        key="unified_file_uploader"
    )
    
    if uploaded_file:
        # 세션 상태에 파일 저장
        st.session_state.last_uploaded_file = uploaded_file

        with st.spinner('🔒 통합 파일 보안 처리 및 영구 저장 중...'):
            # ✅ 새로운 매핑 방식으로 출고 현황 처리
            results, processed_files, mapping_stats = process_unified_file_new(uploaded_file)
            
            # ✅ 새로운 매핑 방식으로 박스 계산 처리
            uploaded_file.seek(0)
            df_for_box = read_excel_file_safely(uploaded_file)
            box_results = {}
            
            if df_for_box is not None:
                df_for_box = sanitize_data(df_for_box)
                if not df_for_box.empty and '수취인이름' in df_for_box.columns:
                    total_boxes, box_e_orders = calculate_box_requirements_new(df_for_box)
                    
                    box_results = {
                        'total_boxes': dict(total_boxes),
                        'box_e_orders': [
                            {
                                'recipient': order['recipient'],
                                'quantities': dict(order['quantities']),
                                'products': dict(order['products'])
                            }
                            for order in box_e_orders
                        ]
                    }
                    
        # 결과 저장
        shipment_saved = save_shipment_data(results) if results else False
        box_saved = save_box_data(box_results) if box_results else False
        
        # ✅ 매핑 성공률 및 기타 제품 표시
        if mapping_stats:
            st.markdown("### 📊 제품 매핑 결과")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "총 처리 주문", 
                    f"{mapping_stats['total_processed']:,}건"
                )
            
            with col2:
                st.metric(
                    "매핑 성공률", 
                    f"{mapping_stats['success_rate']:.1f}%",
                    f"{mapping_stats['successful_mappings']:,}건 성공"
                )
            
            with col3:
                failed_count = mapping_stats['failed_mappings']
                st.metric(
                    "기타 제품", 
                    f"{failed_count}건",
                    f"매핑 실패" if failed_count > 0 else "완벽!"
                )
            
            # 기타 제품 상세 내역 (있을 경우)
            if mapping_stats['failed_mappings'] > 0:
                with st.expander(f"⚠️ 기타로 분류된 제품 내역 ({mapping_stats['failed_mappings']}건)", expanded=False):
                    st.warning("다음 제품들이 '기타'로 분류되었습니다. 제품 매핑 테이블 업데이트가 필요할 수 있습니다.")
                    
                    failure_data = []
                    for failure in mapping_stats['failure_details']:
                        failure_data.append({
                            "행번호": failure['row'],
                            "상품이름": failure['product_name'],
                            "옵션이름": failure['option_name'],
                            "수량": failure['quantity']
                        })
                    
                    if failure_data:
                        failure_df = pd.DataFrame(failure_data)
                        st.dataframe(failure_df, use_container_width=True)
                        
                        # 기타 제품 요약
                        total_other_quantity = sum(failure['quantity'] for failure in mapping_stats['failure_details'])
                        st.info(f"📋 기타 제품 총 수량: {total_other_quantity}개")
        
        # 결과 표시
                if shipment_saved and box_saved:
                    st.success("✅ 출고 현황, 박스 계산 결과가 모두 영구 저장되었습니다!")
                    st.balloons()
                    
                    # 새로고침 버튼 추가
                    if st.button("🔄 페이지 새로고침"):
                        st.rerun()
                else:
                    st.error("❌ 데이터 저장 중 오류가 발생했습니다.")
        
        # ✅ 매핑 모듈 상태 표시 (하단) - if is_admin 블록 외부
        if is_admin:
            with st.expander("🔧 매핑 모듈 정보", expanded=False):
                try:
                    mapping_stats = get_mapping_stats()
                    st.success(f"📊 총 {mapping_stats['total_cases']}개의 매핑 케이스 로드됨")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**제품별 케이스 수:**")
                        for product, count in sorted(mapping_stats['product_stats'].items()):
                            st.write(f"- {product}: {count}개")
                    
                    with col2:
                        st.markdown("**🏗️ 모듈 정보:**")
                        st.write("- **매핑 방식**: O(1) 해시테이블")
                        st.write("- **정확도**: 94개 케이스 완전 매핑")
                        st.write("- **실패 처리**: 기타 제품 자동 분류")
                        st.write("- **패턴**: 싱글톤")
                        
                except Exception as e:
                    st.error(f"❌ 매핑 모듈 로드 실패: {e}")
                    st.warning("💡 product_mapping.py 파일이 같은 폴더에 있는지 확인하세요.")




# 버전 정보
st.markdown("---")
st.markdown("### 🔮 오늘의 운세")

fortune_options = [
    """오늘은 신중함과 계획성이 필요한 날입니다.
특히 금전 관리에서 작은 절약이 큰 도움이 될 거예요. 불필요한 지출을 줄이고 계획적으로 소비해보세요. 투자나 큰 결정은 충분한 정보 수집 후에 하는 것이 현명합니다.""",
    
    """주변 사람들과의 소통에서 오해가 생길 수 있는 하루입니다.
말하기 전에 한 번 더 생각하고, 상대방의 입장도 고려해보세요. 완벽한 관계는 없다는 걸 인정하고 적당한 거리감을 유지하는 것이 좋겠어요. 진솔한 대화 한 번이 억지로 맞춰주는 열 번보다 낫습니다.""",
    
    """업무나 일상에서 예상보다 시간이 오래 걸리는 일들이 있을 수 있어요.
완벽을 추구하기보다는 80% 정도의 완성도로 일단 진행하는 것이 현실적입니다. 동료와의 협업에서는 역할을 명확히 하고, 혼자 모든 걸 해결하려 하지 마세요. 작은 성취라도 스스로 인정해주는 하루가 되길 바랍니다.""",
    
    """몸과 마음이 보내는 신호에 귀 기울여야 할 때입니다.
피곤하면 무리하지 말고 충분히 쉬고, 스트레스가 쌓였다면 가벼운 운동으로 풀어보세요. 완벽한 컨디션보다는 현실적인 관리에 집중하는 것이 좋겠어요. 규칙적인 식사와 수면이 가장 기본적이면서도 효과적인 방법입니다.""",
    
    """모든 일에 대해 평상시보다 더욱 세심한 주의가 필요한 날입니다.
중요한 메시지나 서류는 발송 전에 한 번 더 검토해보세요. 서두르면 실수할 가능성이 높으니 여유 시간을 두고 처리하는 것이 좋겠습니다. 모든 일이 계획대로 되지 않는다는 걸 받아들이고, 플랜 B를 준비해두면 마음이 편할 거예요.""",

"""한계는 오직 당신의 상상 속에만 존재할 뿐입니다.
자신을 믿고 경계를 넘어서는 용기를 가져보세요. 불가능해 보이는 일도 시작하면 가능성이 열립니다. 오늘은 스스로에게 제한을 두지 말고 도전하는 마음으로 임해보세요.""",

"""성공은 매일 반복되는 작은 노력들의 합계입니다.
진전이 느리게 느껴져도 꾸준히 계속 나아가는 것이 중요해요. 큰 변화는 하루아침에 일어나지 않습니다. 작은 실천을 소홀히 하지 말고 일관성 있게 유지해보세요.""",

"""무언가를 위해 더 열심히 노력할수록, 성취했을 때 더 큰 기쁨을 느끼게 됩니다.
노력하는 과정 자체가 성취감의 원천이 될 수 있어요. 쉽게 얻은 것보다는 땀 흘려 이룬 결과가 더 값집니다. 오늘의 수고로움을 미래의 보람으로 바꿔나가세요.""",

"""불가능해 보이는 일도 해내고 나면 당연한 일이 됩니다.
인내와 끈기로 도전을 극복하는 힘을 길러보세요. 처음엔 막막해 보였던 일들도 차근차근 해결할 수 있습니다. 포기하지 않는 마음이 기적을 만들어낼 거예요.""",

"""승리한다는 것이 항상 1등을 의미하지는 않습니다.
때로는 발전과 개선 자체가 더 큰 성공일 수 있어요. 남과 비교하기보다는 어제의 자신보다 나아진 점을 찾아보세요. 개인적인 성장이야말로 진정한 승리입니다.""",

"""인생은 선을 긋는 데 낭비할 수도, 그 선을 넘나드는 데 사용할 수도 있습니다.
안전지대를 벗어나야 성장하고 성공할 수 있어요. 새로운 경험을 두려워하지 말고 적극적으로 받아들여보세요. 변화를 통해서만 진정한 발전이 가능합니다.""",

"""피곤할 때 멈추지 말고, 할 일을 다 끝냈을 때 멈추세요.
피로감을 극복하되 자신의 한계는 존중하는 지혜가 필요합니다. 완주하는 습관이 성취감과 자신감을 키워줄 거예요. 적절한 휴식과 끈기 사이의 균형을 잘 맞춰보세요.""",

"""훌륭한 일을 하는 유일한 방법은 자신이 하는 일을 사랑하는 것입니다.
열정과 목적의식을 따라가면 진정한 성공을 이룰 수 있어요. 의무감보다는 즐거움으로 일할 때 최고의 결과가 나옵니다. 오늘 하는 일에서 의미와 보람을 찾아보세요.""",

"""자신을 믿으면 이미 절반은 성공한 것입니다.
자신감이 성취의 기초가 된다는 것을 기억하세요. 의심과 두려움을 떨쳐내고 자신의 능력을 믿어보세요. 긍정적인 마음가짐이 좋은 결과를 불러올 거예요.""",

"""행복은 도착하는 역이 아니라 여행하는 방식입니다.
목표를 향해 나아가면서도 과정 자체를 즐기는 것이 중요해요. 결과만 바라보지 말고 현재 순간의 의미도 소중히 여기세요. 매일매일이 소중한 여행의 한 부분임을 잊지 마세요.""",
    
    """새로운 배움과 성장의 기회가 찾아오는 의미 있는 하루입니다.
평소 관심 있던 분야에 대해 조금 더 깊이 알아보는 시간을 가져보세요. 작은 호기심이 큰 변화의 시작이 될 수 있습니다. 실패를 두려워하지 말고, 시행착오도 성장의 과정이라고 생각하며 도전해보세요.""",
    
    """중요한 결정을 내려야 하는 상황이 생길 수 있어요.
감정적인 판단보다는 객관적인 사실에 근거해서 결정하는 것이 좋겠습니다. 주변 사람들의 의견도 들어보되, 최종 결정은 본인의 가치관에 따라 내리세요. 완벽한 선택은 없다는 걸 받아들이고, 선택 후에는 후회하지 마세요.""",
    
    """변화에 유연하게 적응하는 능력이 중요한 날입니다.
예상과 다른 상황이 벌어져도 당황하지 말고 차분히 대응해보세요. 변화를 부정적으로만 보지 말고, 새로운 기회로 받아들이는 마음가짐이 필요합니다. 고정관념에서 벗어나 다른 관점으로 바라보면 해결책이 보일 거예요.""",
    
    """대화와 소통에서 특별히 주의가 필요한 하루입니다.
듣는 것이 말하는 것보다 더 중요할 수 있어요. 상대방의 말을 끝까지 들어보고 이해하려고 노력해보세요. 자신의 의견을 전달할 때는 명확하되 부드럽게, 비판보다는 건설적인 제안으로 접근하는 것이 효과적입니다.""",
    
    """바쁜 일상 속에서 잠깐의 여유를 찾는 것이 중요한 날입니다.
모든 일을 다 해내려고 무리하지 말고, 우선순위를 정해서 하나씩 처리해보세요. 완벽하지 않아도 괜찮다는 마음으로 자신을 너그럽게 대해주세요. 짧은 휴식이라도 취하면 오히려 효율이 더 올라갈 거예요.""",
    
    """집중력을 발휘해야 하는 중요한 과제들이 있는 날입니다.
산만한 환경을 정리하고 한 번에 하나씩만 처리하는 것이 좋겠어요. 멀티태스킹보다는 순차적으로 집중해서 완료하는 것이 더 효율적입니다. 중간중간 5분 정도 눈을 쉬어주면 집중력을 더 오래 유지할 수 있어요.""",
    
    """창의적인 아이디어가 필요한 상황에서 빛을 발할 수 있는 날입니다.
기존의 방식에 얽매이지 말고 다른 각도에서 접근해보세요. 브레인스토밍이나 마인드맵을 활용해서 생각을 정리해보는 것도 좋습니다. 완전히 새로운 것보다는 기존 아이디어를 조합하는 것에서 시작해보세요.""",
    
    """문제 해결 능력을 시험받는 하루가 될 것 같아요.
복잡해 보이는 문제도 작은 단위로 나누어서 하나씩 해결해보세요. 혼자 끙끙 앓지 말고 적절한 도움을 요청하는 것도 현명한 방법입니다. 문제 자체에만 매몰되지 말고 해결 방법에 집중하면 길이 보일 거예요.""",
    
    """시간 관리가 특히 중요한 의미를 갖는 날입니다.
해야 할 일들의 마감일과 중요도를 다시 한 번 점검해보세요. 급한 일과 중요한 일을 구분해서 우선순위를 정하는 것이 필요합니다. 여유 시간을 조금이라도 확보해두면 예상치 못한 상황에 대처하기 수월할 거예요.""",

    """오늘은 새로운 도전을 시도해보기에 적합한 날입니다.
두려움을 떨치고 한 걸음 내딛으면 생각보다 많은 것을 얻을 수 있을 거예요. 실패해도 괜찮으니 용기를 가지세요. 작은 도전이라도 시작하는 것 자체가 이미 성공의 첫 걸음입니다.""",
    
    """소소한 일상 속에서 작은 행복을 발견할 수 있는 하루입니다.
지나친 욕심을 버리고 지금 가진 것에 감사하는 마음을 가져보세요. 만족감이 더 큰 에너지로 돌아올 것입니다. 커피 한 잔의 여유나 따뜻한 햇살 같은 것에서도 기쁨을 찾을 수 있을 거예요.""",
    
    """오늘은 주변 사람들의 도움이 예상외로 큰 힘이 될 수 있습니다.
필요할 땐 주저하지 말고 도움을 요청하세요. 혼자가 아니라는 것을 기억하는 것만으로도 안심이 될 거예요. 때로는 남에게 의존하는 것도 용기이며, 상호부조가 관계를 더욱 돈독하게 만듭니다.""",
    
    """건강에 특히 신경 써야 하는 날입니다.
평소보다 충분한 수분 섭취와 적절한 휴식을 취하는 것을 잊지 마세요. 작은 습관이 큰 변화를 만들 수 있습니다. 목과 어깨를 가볍게 스트레칭하거나 눈을 자주 쉬어주는 것만으로도 컨디션이 좋아질 거예요.""",
    
    """급하게 서두르기보다는 차분한 마음으로 하루를 보내는 것이 좋습니다.
계획을 세우고 하나씩 차근차근 처리해나가면 생각보다 성과가 더 클 거예요. 성급함은 실수를 부르지만, 침착함은 효율을 높입니다. 깊게 숨을 쉬고 마음을 가라앉히며 시작해보세요.""",
    
    """자신만의 시간과 공간을 확보하는 것이 필요한 날입니다.
바쁜 일상에서 벗어나 잠시 혼자만의 시간을 가져보세요. 마음의 평화를 찾는 데 도움이 될 것입니다. 독서나 음악 감상, 또는 단순히 창밖을 바라보는 것만으로도 충분한 힐링이 될 수 있어요.""",
    
    """예상치 못한 변화나 상황이 생길 수 있는 하루입니다.
당황하지 말고 유연하게 대처하며 긍정적인 태도를 유지하는 것이 중요합니다. 변화는 때로 불편하지만 성장을 위한 기회가 될 것입니다. 적응력을 발휘하면 오히려 더 좋은 결과를 얻을 수도 있어요.""",
    
    """오늘은 자신의 감정을 솔직하게 인정하고 표현하는 것이 좋습니다.
억압하지 말고 적절한 방법으로 감정을 드러내보세요. 마음의 부담이 한결 가벼워질 거예요. 감정 일기를 쓰거나 신뢰하는 사람과 대화를 나누는 것도 좋은 방법입니다.""",
    
    """중요한 결정이나 선택의 기로에 서게 될 수 있는 날입니다.
주변의 조언을 듣되 최종 결정은 본인의 가치관에 따라 내리세요. 급하게 결정하기보다는 충분한 시간을 두고 신중히 고민하는 자세가 필요합니다. 직감도 중요하지만 논리적 판단도 함께 고려해보세요.""",
    
    """작은 성취와 진전도 스스로 인정하고 격려해주는 하루가 되세요.
완벽을 추구하기보다는 꾸준한 노력과 점진적인 개선에 집중하는 것이 좋겠습니다. 자신에게 너무 엄격하지 말고 친절한 마음으로 대해주세요. 오늘 하루도 최선을 다한 자신에게 감사의 마음을 전해보세요.""",
    
    """감정의 기복이 있을 수 있지만 잘 관리할 수 있는 날입니다.
기분이 좋지 않다면 억지로 참지 말고 적절한 방법으로 표현해보세요. 깊게 호흡하거나 잠깐 산책하는 것만으로도 마음이 진정될 수 있어요. 부정적인 감정도 자연스러운 것이니 자책하지 말고, 곧 지나갈 것이라고 생각하세요."""
]

# 운세 버튼 및 애니메이션 효과
if st.button("🎲 오늘의 운세 확인하기", key="fortune"):
    
    # 1단계: 주사위 애니메이션 (스피너 사용)
    with st.spinner("🎲 운명의 주사위가 굴러가는 중..."):
        time.sleep(1.5)  # 1.5초 대기로 긴장감 조성
    
    # 2단계: 결과 알림
    st.success("🎯 당신의 운세가 결정되었습니다!")
    
    # 3단계: 운세 선택 및 분석
    today_fortune = random.choice(fortune_options)
    lines = today_fortune.strip().split('\n')
    summary = lines[0]  # 한줄평
    details = '\n'.join(lines[1:]).strip()  # 세부사항
    
    
    # 4단계: 운세 내용 표시
    with st.container():
        st.markdown("#### 🔮 오늘의 한줄평")
        st.info(summary)
        
        st.markdown("#### 📝 세부사항")
        st.success(details)
