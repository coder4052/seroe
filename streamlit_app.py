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



# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

# GitHub 설정 - 수정된 저장소명
REPO_OWNER = "coder4052"  # 본인 GitHub 사용자명으로 변경하세요
REPO_NAME = "seroe"  # 실제 생성한 저장소명
SHIPMENT_FILE_PATH = "data/출고현황_encrypted.json"
BOX_FILE_PATH = "data/박스계산_encrypted.json"
STOCK_FILE_PATH = "data/재고현황_encrypted.json"

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
    """민감정보 완전 제거 - 박스 계산용"""
    safe_columns = ['상품이름', '옵션이름', '상품수량', '수취인이름', '주문자이름', '주문자전화번호1']
    
    available_columns = df.columns.intersection(safe_columns)
    sanitized_df = df[available_columns].copy()
    
    essential_columns = ['상품이름', '옵션이름', '상품수량']
    missing_columns = [col for col in essential_columns if col not in sanitized_df.columns]
    if missing_columns:
        st.error(f"❌ 필수 컬럼이 없습니다: {missing_columns}")
        st.info("💡 엑셀 파일의 컬럼명을 확인하세요: G열(상품이름), H열(옵션이름), N열(상품수량)")
        return pd.DataFrame()
    
    st.success(f"✅ 필수 컬럼 정상 처리: {list(available_columns)}")
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


# 🎯 출고 현황 처리 함수들
def extract_product_from_option(option_text):
    """옵션에서 상품 분류 추출 (H열 우선)"""
    if pd.isna(option_text):
        return "기타"
    
    option_text = str(option_text).lower()
    
    if "단호박식혜" in option_text:
        return "단호박식혜"
    elif "일반식혜" in option_text or ("식혜" in option_text and "단호박" not in option_text):
        return "식혜"
    elif "수정과" in option_text:
        return "수정과"
    elif "쌀요거트" in option_text or "요거트" in option_text or "플레인" in option_text:
        return "플레인 쌀요거트"
    
    return "기타"

def extract_product_from_name(product_name):
    """상품이름에서 분류 추출 (G열 - 보조용)"""
    if pd.isna(product_name):
        return "기타"
    
    product_name = str(product_name).lower()
    
    bracket_match = re.search(r'\[서로\s+([^\]]+)\]', product_name)
    if bracket_match:
        product_key = bracket_match.group(1).strip()
        
        if "단호박식혜" in product_key:
            return "단호박식혜"
        elif "진하고 깊은 식혜" in product_key or "식혜" in product_key:
            return "식혜"
        elif "수정과" in product_key:
            return "수정과"
        elif "쌀요거트" in product_key:
            return "플레인 쌀요거트"
    
    if "쌀요거트" in product_name or "요거트" in product_name or "플레인" in product_name:
        return "플레인 쌀요거트"
    
    return "기타"

def parse_option_info(option_text):
    """옵션에서 수량과 용량 추출"""
    if pd.isna(option_text):
        return 1, ""
    
    option_text = str(option_text)
    
    # 패턴 1: "5개, 240ml" 또는 "10개, 500ml"
    pattern1 = re.search(r'(\d+)개,\s*(\d+(?:\.\d+)?(?:ml|L))', option_text)
    if pattern1:
        return int(pattern1.group(1)), pattern1.group(2)
    
    # 패턴 2: "2, 1L" 또는 "4, 1L"
    pattern2 = re.search(r'(\d+),\s*(\d+(?:\.\d+)?(?:ml|L))', option_text)
    if pattern2:
        return int(pattern2.group(1)), pattern2.group(2)
    
    # 패턴 3: "용량 : 1L 2병"
    pattern3 = re.search(r'용량\s*:\s*(\d+(?:\.\d+)?(?:ml|L))\s*(\d+)병', option_text)
    if pattern3:
        return int(pattern3.group(2)), pattern3.group(1)
    
    # 패턴 4: "500ml 3병" 또는 "500ml 5병"
    pattern4 = re.search(r'(\d+(?:\.\d+)?(?:ml|L))\s*(\d+)병', option_text)
    if pattern4:
        return int(pattern4.group(2)), pattern4.group(1)
    
    # 패턴 5: 단순 용량만 "플레인 쌀요거트 1L"
    capacity_match = re.search(r'(\d+(?:\.\d+)?(?:ml|L))', option_text)
    if capacity_match:
        return 1, capacity_match.group(1)
    
    return 1, ""

def standardize_capacity(capacity):
    """용량 표준화 - 출고 현황용 (200ml 그대로 표시)"""
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
        return "200ml"
    
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

# 📦 박스 계산 함수들
def group_orders_by_recipient(df):
    """수취인별로 주문을 그룹화하여 박스 계산 - 동명이인 구분 개"""
    orders = defaultdict(dict)
    
    for _, row in df.iterrows():
        # 복합 키 생성: 수취인이름 + 주문자이름으로 동명이인 구
        recipient_name = row.get('수취인이름', '알 수 없음')
        orderer_name = row.get('주문자이름', '').strip()

        # 고유 식별자 생성
        if orderer_name and orderer_name != recipient_name:
            recipient_key = f"{recipient_name} - 주문자: {orderer_name}"
        else:
            recipient_key = f"{recipient_name} - 직접주문"
        
        # 상품 정보 추출
        option_product = extract_product_from_option(row.get('옵션이름', ''))
        name_product = extract_product_from_name(row.get('상품이름', ''))
        final_product = option_product if option_product != "기타" else name_product
        
        # 수량 및 용량 정보
        option_quantity, capacity = parse_option_info(row.get('옵션이름', ''))
        
        try:
            base_quantity = int(row.get('상품수량', 1))
        except (ValueError, TypeError):
            base_quantity = 1
        
        total_quantity = base_quantity * option_quantity
        standardized_capacity = standardize_capacity_for_box(capacity)
        
        if standardized_capacity:
            key = f"{final_product} {standardized_capacity}"
        else:
            key = final_product
        
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

def calculate_box_requirements(df):
    """전체 박스 필요량 계산 - 새로운 로직"""
    orders = group_orders_by_recipient(df)
    
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

def process_unified_file(uploaded_file):
    """통합 엑셀 파일 처리 - 출고 현황용 (개선된 메모리 관리)"""
    try:
        df = read_excel_file_safely(uploaded_file)
        
        if df is None:
            return {}, []
        
        df = sanitize_data(df)
        
        if df.empty:
            return {}, []
        
        st.write(f"📄 **{uploaded_file.name}**: 통합 파일 처리 시작 (총 {len(df):,}개 주문)")
        
        results = defaultdict(int)
        
        # 프로그레스 바 추가
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_rows = len(df)
        
        for index, row in df.iterrows():
            # 프로그레스 업데이트
            progress = (index + 1) / total_rows
            progress_bar.progress(progress)
            status_text.text(f"처리 중... {index + 1:,}/{total_rows:,} ({progress:.1%})")
            
            option_product = extract_product_from_option(row.get('옵션이름', ''))
            name_product = extract_product_from_name(row.get('상품이름', ''))
            final_product = option_product if option_product != "기타" else name_product
            
            option_quantity, capacity = parse_option_info(row.get('옵션이름', ''))
            
            try:
                base_quantity = int(row.get('상품수량', 1))
            except (ValueError, TypeError):
                base_quantity = 1
                
            total_quantity = base_quantity * option_quantity
            
            standardized_capacity = standardize_capacity(capacity)
            
            if standardized_capacity:
                key = f"{final_product} {standardized_capacity}"
            else:
                key = final_product
            
            results[key] += total_quantity
        
        # 프로그레스 바 정리
        progress_bar.empty()
        status_text.empty()
        
        processed_files = [f"통합 파일 ({len(df):,}개 주문)"]
        
        # 메모리 정리 추가
        del df
        gc.collect()
        
        return results, processed_files
        
    except Exception as e:
        st.error(f"❌ {uploaded_file.name} 처리 중 오류: {str(e)}")
        return {}, []

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

        #col1, col2 있던 곳
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

        # 여기에 BOX_DESCRIPTIONS 추가
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
                    "주문 번호": f"주문 {i}",
                    "수취인": order.get('recipient', '알 수 없음'),
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

# 세 번째 탭: 재고 관리
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
    
    # 출고 현황과 동기화된 상품 키 가져오기 + 추가 필수 상품
    shipment_results, _ = load_shipment_data()
    
    # 기본 상품 키 목록 (출고 현황 기반)
    product_keys = set()
    if shipment_results:
        product_keys.update(shipment_results.keys())
    
    # 추가 필수 상품 목록 (수동 추가 - 밥알없는 제품 포함)
    additional_products = [
        "단호박식혜 240ml",
        "식혜 1.5L",
        "식혜 240ml",
        "밥알없는 단호박식혜 1.5L",
        "밥알없는 단호박식혜 1L",
        "밥알없는 단호박식혜 240ml",
        "밥알없는 식혜 1.5L",
        "밥알없는 식혜 1L",
        "밥알없는 식혜 240ml",
        "플레인 쌀요거트 200ml"
    ]
    
    product_keys.update(additional_products)
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
                st.markdown("<br>", unsafe_allow_html=True)  # 이 줄을 추가
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

            #col1, col2, col3 자리
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
                        
            # 저장 버튼있던 곳
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
                            
                            stock_input[f"{product_name}|{capacity}"] = st.number_input(
                                f"{capacity}",
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
                    
                    stock_input[f"{product_name}|{capacity}"] = st.number_input(
                        f"{capacity}",
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

# 관리자 파일 업로드 (tab3 밖에서)
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
    """)
    
    uploaded_file = st.file_uploader(
        "📁 통합 엑셀 파일을 업로드하세요 (.xlsx만 지원)",
        type=['xlsx'],
        help="통합 출고내역서(.xlsx)를 업로드하세요. 고객 정보는 자동으로 제거됩니다.",
        key="unified_file_uploader"
    )
    
    #if uploaded_file: 있던 곳
    if uploaded_file:
        # 세션 상태에 파일 저장
        st.session_state.last_uploaded_file = uploaded_file

        with st.spinner('🔒 통합 파일 보안 처리 및 영구 저장 중...'):
            # 출고 현황 처리 및 저장
            results, processed_files = process_unified_file(uploaded_file)
            
            # 박스 계산 처리
            uploaded_file.seek(0)
            df_for_box = read_excel_file_safely(uploaded_file)
            box_results = {}
            
            if df_for_box is not None:
                df_for_box = sanitize_data(df_for_box)
                if not df_for_box.empty and '수취인이름' in df_for_box.columns:
                    total_boxes, box_e_orders = calculate_box_requirements(df_for_box)
                    
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
                    
        # 결과 표시 (기존 코드 수정)
        shipment_saved = save_shipment_data(results) if results else False
        box_saved = save_box_data(box_results) if box_results else False
        
        # 결과 표시
        if shipment_saved and box_saved:
            st.success("✅ 출고 현황, 박스 계산 결과가 모두 영구 저장되었습니다!")
        else:
            st.error("❌ 데이터 저장 중 오류가 발생했습니다.")


# 버전 정보
st.markdown("---")
st.markdown("### 🔮 오늘의 운세")

fortune_messages = [
    "💰 재물운: 오늘은 돈 관리에 대해 다시 생각해볼 좋은 날입니다. 큰 수익보다는 작은 절약이 더 확실한 도움이 될 거예요. 불필요한 지출을 줄이고 계획적으로 소비하면 한 달 후 차이를 느낄 수 있을 것 같습니다. 투자나 큰 결정은 충분한 정보 수집 후에 하는 것이 좋겠어요.",
    "🤝 인간관계운: 오늘은 주변 사람들과의 소통에서 약간의 오해가 생길 수 있는 날입니다. 말하기 전에 한 번 더 생각하고, 상대방의 입장도 고려해보세요. 완벽한 관계는 없다는 걸 인정하고 적당한 거리감을 유지하는 것이 현명할 것 같습니다. 진솔한 대화 한 번이 억지로 맞춰주는 열 번보다 낫습니다.",
    "💼 직장운: 업무에서 예상보다 시간이 오래 걸리는 일들이 있을 수 있어요. 완벽을 추구하기보다는 80% 정도의 완성도로 일단 진행하는 것이 좋겠습니다. 동료와의 협업에서는 역할 분담을 명확히 하고, 혼자 모든 걸 해결하려 하지 마세요. 작은 성취라도 스스로 인정해주는 하루가 되길 바랍니다.",    
    "🏥 건강운: 몸이 보내는 신호에 좀 더 귀 기울여야 할 때입니다. 피곤하면 무리하지 말고 충분히 쉬고, 스트레스가 쌓였다면 가벼운 운동이나 산책으로 풀어보세요. 완벽한 건강보다는 컨디션 관리에 집중하는 것이 현실적입니다. 규칙적인 식사와 수면 패턴이 가장 기본이면서도 가장 효과적인 관리법이에요.",   
    "⚠️ 신중운: 오늘은 평상시보다 더욱 세심한 주의가 필요한 날입니다. 특히 중요한 메시지나 서류는 발송 전에 한 번 더 검토해보세요. 서두르면 실수할 가능성이 높으니 여유 시간을 두고 일처리를 하는 것이 좋겠습니다. 모든 일이 계획대로 되지 않는다는 걸 받아들이고, 플랜 B를 준비해두면 마음이 편할 거예요."
]

if st.button("🎲 오늘의 운세 확인하기", key="fortune"):
    today_fortune = random.choice(fortune_options)
    st.success(today_fortune)
