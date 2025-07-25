# product_mapping.py
"""
제품-옵션 매핑 테이블 모듈 (streamlit_app용)

이 모듈은 출고내역서의 상품이름과 옵션이름을 
표준화된 제품분류, 용량, 개수로 매핑합니다.

사용법:
    from product_mapping import get_product_info
    
    result = get_product_info("서로 식혜", "2개, 1000ml")
    # 결과: ("식혜", "1L", 2)
"""

import pandas as pd

class ProductMapper:
    """제품 매핑 처리 클래스"""
    
    def __init__(self):
        """매핑 테이블 초기화"""
        self.mapping_table = self._build_complete_mapping_table()
        print(f"✅ ProductMapper 초기화 완료: {len(self.mapping_table)}개 케이스 로드됨")
    
    def _build_complete_mapping_table(self):
        """완전한 94개 매핑 테이블 생성"""
        mapping = {}
        
        # 기본 케이스들 (8개)
        basic_cases = [
            ("플레인 쌀요거트:", "플레인 쌀요거트 200ml", "플레인 쌀요거트", "200ml", 1),
            ("플레인 쌀요거트:", "플레인 쌀요거트 1L", "플레인 쌀요거트", "1L", 1),
            ("플레인 200ml", "서로 쌀요거트 플레인 무설탕 무유당 비건, 1개, 200ml", "플레인 쌀요거트", "200ml", 1),
            ("플레인 200ml", "서로 쌀요거트 플레인 무설탕 무유당 비건, 1, 200ml", "플레인 쌀요거트", "200ml", 1),  # ← 추가
            ("[서로 쌀요거트] 쌀누룩 비건 요거트 무설탕 마시는요거트 수제 대용량 플레인 1L", "", "플레인 쌀요거트", "1L", 1),  # 공란 케이스
            ("[서로 쌀요거트] 무설탕 수제 비건 마시는요거트", "[서로 쌀요거트] 무설탕 수제 비건 마시는요거트 : 200ml 5병", "플레인 쌀요거트", "200ml", 5),
            ("서로 식혤", "2개, 1000ml", "식혜", "1L", 2),
            ("서로 단호박식혜", "2개, 1000ml", "단호박식혜", "1L", 2),
            ("단호박식혜", "[서로 ] 수제 단호박 통째로, 10개, 240ml", "단호박식혜", "240ml", 10),
        ]
        
        # 기본 케이스 추가
        for case_data in basic_cases:
            key = (case_data[0], case_data[1])
            mapping[key] = (case_data[2], case_data[3], case_data[4])
        
        # 동적 케이스들 추가
        mapping.update(self._build_dynamic_cases())
        
        return mapping
    
    def _build_dynamic_cases(self):
        """동적 케이스들 생성 (86개)"""
        dynamic_mapping = {}
        
        # 케이스 4: 서로 플레인 쌀요거트 (1~4개)
        for count in range(1, 5):
            key = ("서로 플레인 쌀요거트", f"{count}개, 1000ml")
            dynamic_mapping[key] = ("플레인 쌀요거트", "1L", count)
        
        # 케이스 5: 서로 쌀요거트 플레인 무가당 무유당 비건 (1~4개, "개" 포함)
        for count in range(1, 5):
            key = ("서로 쌀요거트 플레인 무가당 무유당 비건", f"{count}개, 1L")
            dynamic_mapping[key] = ("플레인 쌀요거트", "1L", count)
        
        # 케이스 6: 서로 쌀요거트 플레인 무가당 무유당 비건 (1~4개, "개" 없음)
        for count in range(1, 5):
            key = ("서로 쌀요거트 플레인 무가당 무유당 비건", f"{count}, 1L")
            dynamic_mapping[key] = ("플레인 쌀요거트", "1L", count)
        
        # 케이스 7: 서로 쌀요거트 플레인 무가당 무유당 비건 (1~4개, 1000ml)
        for count in range(1, 5):
            key = ("서로 쌀요거트 플레인 무가당 무유당 비건", f"{count}, 1000ml")
            dynamic_mapping[key] = ("플레인 쌀요거트", "1L", count)
        
        # 케이스 11: [서로 ] 수제 단호박 통째로 (2~6개)
        for count in range(2, 7):
            key = ("단호박식혜", f"[서로 ] 수제 단호박 통째로, {count}개, 1L")
            dynamic_mapping[key] = ("단호박식혜", "1L", count)
        
        # 케이스 12: 자일로스설탕... (2~4개)
        for count in range(2, 5):
            key = ("단호박식혜", f" 자일로스설탕 밥알없는 단유 수제 감주 호박 식혜, {count}개, 1L")
            dynamic_mapping[key] = ("단호박식혜", "1L", count)
        
        # 케이스 13: [서로 진하고 깊은 식혜] (2~10개, 240ml/1L)
        for count in range(2, 11):
            for capacity in ["240ml", "1L"]:
                key = ("[서로 진하고 깊은 식혜] 전통 국산 수제 식혜", f"{count}개, {capacity}")
                dynamic_mapping[key] = ("식혜", capacity, count)
        
        # 케이스 16: [서로 식혜] 수제 전통 국산 엿기름 (2~5개, 240ml/1L)
        for count in range(2, 6):
            for capacity in ["240ml", "1L"]:
                key = ("[서로 식혜] 수제 전통 국산 엿기름", f"서로 식혤 : {capacity} {count}병")
                dynamic_mapping[key] = ("식혜", capacity, count)

        # ✅ 먼저 capacities_17 정의        
        capacities_17 = [("240ml", 2), ("1L", 1), ("1.5L", 1)]
        
        # ✅ 추가: "2병" 표기가 있는 케이스들
        for capacity, count in capacities_17:
            if capacity == "240ml":  # 240ml만 "2병" 표기 추가
                key = ("[서로 식혜] 1L 호박식혜 단호박식혜 수제 전통 국산 엿기름", f"서로 식혜: 단호박식혜 / 용량: {capacity} {count}병")
                dynamic_mapping[key] = ("단호박식혜", capacity, count)
                
                key = ("[서로 식혤] 1L 호박식혜 단호박식혜 수제 전통 국산 엿기름", f"서로 식혜: 일반식혜 / 용량: {capacity} {count}병")
                dynamic_mapping[key] = ("식혤", capacity, count)

        # 케이스 17: 단호박식혜 (240ml는 2개 고정, 1L/1.5L은 1개)
        for capacity, count in capacities_17:
            key = ("[서로 식혜] 1L 호박식혜 단호박식혜 수제 전통 국산 엿기름", f"서로 식혜: 단호박식혜 / 용량: {capacity}")
            dynamic_mapping[key] = ("단호박식혜", capacity, count)
        
        # 케이스 18: 일반식혜 (240ml는 2개 고정, 1L/1.5L은 1개)
        for capacity, count in capacities_17:
            key = ("[서로 식혜] 1L 호박식혜 단호박식혜 수제 전통 국산 엿기름", f"서로 식혜: 일반식혜 / 용량: {capacity}")
            dynamic_mapping[key] = ("식혜", capacity, count)
        
        # 케이스 19: [서로 수정과] 수제 전통 (3, 5, 10개)
        for count in [3, 5, 10]:
            key = ("[서로 수정과] 수제 전통", f"{count}개, 500ml")
            dynamic_mapping[key] = ("수정과", "500ml", count)
        
        # 케이스 20, 21: [서로 수정과] 500ml 수제 전통
        dynamic_mapping[("[서로 수정과] 500ml 수제 전통", "서로 수정과 : 500ml 3병")] = ("수정과", "500ml", 3)
        dynamic_mapping[("[서로 수정과] 500ml 수제 전통", "서로 수정과 : 500ml 5병")] = ("수정과", "500ml", 5)
        
        # 케이스 22: [서로 수정과] 500ml 3병 피라미딩... (3, 5개)
        for count in [3, 5]:
            key = ("[서로 수정과] 500ml 3병 피라미딩 수정과 수제 전통", f"서로 수정과 500ml: 500ml {count}병")
            dynamic_mapping[key] = ("수정과", "500ml", count)
        
        # 케이스 23: [서로 단호박식혜] 수제 전통 1L... (1~10병, 240ml는 5,10개만)
        for count in range(1, 11):
            key = ("[서로 단호박식혜] 수제 전통 1L 국산 엿기름", f"서로 단호박식혜 : 단호박식혜, 용량 : 1L {count}병")
            dynamic_mapping[key] = ("단호박식혜", "1L", count)
        
        for count in [5, 10]:  # 240ml는 5, 10개만
            key = ("[서로 단호박식혜] 수제 전통 1L 국산 엿기름", f"서로 단호박식혜 : 단호박식혜, 용량 : 240ml {count}병")
            dynamic_mapping[key] = ("단호박식혜", "240ml", count)
        
        # 케이스 24: [서로 단호박식혜] 수제 단호박 통째로 (2~10개, 240ml는 5,10개만)
        for count in range(2, 11):
            key = ("[서로 단호박식혜] 수제 단호박 통째로", f"{count}개, 1L")
            dynamic_mapping[key] = ("단호박식혜", "1L", count)
        
        for count in [5, 10]:  # 240ml는 5, 10개만
            key = ("[서로 단호박식혜] 수제 단호박 통째로", f"{count}개, 240ml")
            dynamic_mapping[key] = ("단호박식혜", "240ml", count)
        
        return dynamic_mapping
    
    def get_product_info(self, product_name, option_name):
        """
        제품 정보 추출 (이중 매핑 시도)
        
        Args:
            product_name (str): 상품이름
            option_name (str): 옵션이름 (공란 가능)
        
        Returns:
            tuple: (제품분류, 용량, 개수)
        """
        # 공란 처리
        if pd.isna(option_name) or option_name is None:
            option_name = ""
        
        # ✅ 1차 시도: 원본 키로 매핑 (공백 보존 - 자일로스 케이스용)
        original_key = (str(product_name), str(option_name))
        if original_key in self.mapping_table:
            return self.mapping_table[original_key]
        
        # ✅ 2차 시도: strip() 적용한 키로 매핑 (공백 제거 - 일반 케이스용)
        stripped_key = (str(product_name).strip(), str(option_name).strip())
        if stripped_key in self.mapping_table:
            return self.mapping_table[stripped_key]
        
        # 둘 다 실패하면 기타로 분류
        return ("기타", "", 1)    
        
    def get_mapping_stats(self):
        """
        매핑 테이블 통계 정보
        
        Returns:
            dict: 매핑 통계 정보
        """
        product_stats = {}
        for (product_name, option_name), (product_type, capacity, count) in self.mapping_table.items():
            if product_type not in product_stats:
                product_stats[product_type] = 0
            product_stats[product_type] += 1
        
        return {
            'total_cases': len(self.mapping_table),
            'product_stats': product_stats
        }
    
    def validate_sample_data(self, sample_data):
        """
        샘플 데이터로 매핑 검증
        
        Args:
            sample_data (list): [(product_name, option_name), ...] 형태의 리스트
        
        Returns:
            dict: 검증 결과
        """
        results = []
        for product_name, option_name in sample_data:
            result = self.get_product_info(product_name, option_name)
            success = result[0] != "기타"
            results.append({
                'product_name': product_name,
                'option_name': option_name,
                'result': result,
                'success': success
            })
        
        success_count = sum(1 for r in results if r['success'])
        success_rate = (success_count / len(results)) * 100 if results else 0
        
        return {
            'results': results,
            'success_count': success_count,
            'total_count': len(results),
            'success_rate': success_rate
        }

# 전역 매퍼 인스턴스 (싱글톤 패턴)
_product_mapper = None

def get_product_mapper():
    """
    전역 ProductMapper 인스턴스 반환 (싱글톤)
    
    Returns:
        ProductMapper: 매퍼 인스턴스
    """
    global _product_mapper
    if _product_mapper is None:
        _product_mapper = ProductMapper()
    return _product_mapper

# 편의 함수들 (메인 코드에서 쉽게 사용할 수 있도록)
def get_product_info(product_name, option_name):
    """
    제품 정보 추출 편의 함수
    
    Args:
        product_name (str): 상품이름
        option_name (str): 옵션이름
    
    Returns:
        tuple: (제품분류, 용량, 개수)
    """
    mapper = get_product_mapper()
    return mapper.get_product_info(product_name, option_name)

def get_mapping_stats():
    """매핑 통계 정보 편의 함수"""
    mapper = get_product_mapper()
    return mapper.get_mapping_stats()

def validate_sample_data(sample_data):
    """샘플 데이터 검증 편의 함수"""
    mapper = get_product_mapper()
    return mapper.validate_sample_data(sample_data)

# 모듈 테스트 코드 (직접 실행 시에만)
if __name__ == "__main__":
    print("🧪 product_mapping.py 모듈 테스트")
    print("=" * 50)
    
    # 매퍼 초기화 및 통계
    mapper = get_product_mapper()
    stats = get_mapping_stats()
    
    print(f"✅ 총 {stats['total_cases']}개의 매핑 케이스 로드 완료!")
    print("\n📊 제품별 케이스 수:")
    for product, count in sorted(stats['product_stats'].items()):
        print(f"  - {product}: {count}개")
    
    # 샘플 테스트
    print("\n🧪 샘플 매핑 테스트:")
    test_cases = [
        ("서로 식혜", "2개, 1000ml"),
        ("[서로 수정과] 수제 전통", "10개, 500ml"),
        ("[서로 쌀요거트] 쌀누룩 비건 요거트 무설탕 마시는요거트 수제 대용량 플레인 1L", ""),
        ("없는제품", "없는옵션")  # 실패 케이스
    ]
    
    for product_name, option_name in test_cases:
        result = get_product_info(product_name, option_name)
        status = "✅" if result[0] != "기타" else "❌"
        print(f"{status} '{product_name}' + '{option_name}' → {result}")
    
    # 검증 결과
    validation = validate_sample_data(test_cases)
    print(f"\n📈 테스트 결과: {validation['success_count']}/{validation['total_count']} ({validation['success_rate']:.1f}%)")
    
    print("\n🎉 모듈 테스트 완료!")
