import requests
import os
import json
import argparse
from typing import List, Dict, Any, Optional
import time

class ImageAnalysisClient:
    """PDF에서 추출된 이미지를 분석하기 위한 클라이언트"""
    
    def __init__(self, server_url: str = "http://localhost:5050"):
        """
        클라이언트 초기화
        
        Args:
            server_url: 이미지 분석 서버 URL
        """
        self.server_url = server_url.rstrip('/')
        
    def check_server_health(self) -> Dict[str, Any]:
        """서버 상태 확인"""
        response = requests.get(f"{self.server_url}/health")
        response.raise_for_status()
        return response.json()
    
    def analyze_image(self, image_path: str, lang: str = "eng") -> Dict[str, Any]:
        """
        단일 이미지 분석
        
        Args:
            image_path: 이미지 파일 경로
            lang: OCR 언어 (기본값: eng, 한국어: kor, 한국어+영어: kor+eng)
            
        Returns:
            분석 결과 딕셔너리
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(
                f"{self.server_url}/analyze/ocr",
                files=files,
                params={'lang': lang}
            )
            response.raise_for_status()
            return response.json()
    
    def analyze_images_batch(self, image_paths: List[str], lang: str = "eng") -> Dict[str, Any]:
        """
        여러 이미지 일괄 분석
        
        Args:
            image_paths: 이미지 파일 경로 목록
            lang: OCR 언어 (기본값: eng, 한국어: kor, 한국어+영어: kor+eng)
            
        Returns:
            분석 결과 딕셔너리 목록
        """
        files = []
        
        for path in image_paths:
            if not os.path.exists(path):
                print(f"경고: 이미지 파일을 찾을 수 없습니다: {path}")
                continue
                
            files.append(('files', (os.path.basename(path), open(path, 'rb'), 'image/jpeg')))
        
        if not files:
            raise ValueError("분석할 유효한 이미지 파일이 없습니다")
        
        response = requests.post(
            f"{self.server_url}/analyze/ocr/batch",
            files=files,
            params={'lang': lang}
        )
        
        # 파일 핸들 닫기
        for _, file_tuple, _ in files:
            file_tuple[1].close()
            
        response.raise_for_status()
        return response.json()
    
    def analyze_from_path(self, image_path: str, lang: str = "eng") -> Dict[str, Any]:
        """
        서버에 있는 이미지 경로로 분석 (서버와 클라이언트가 같은 파일 시스템을 공유할 때 유용)
        
        Args:
            image_path: 서버에 있는 이미지 파일 경로
            lang: OCR 언어 (기본값: eng, 한국어: kor, 한국어+영어: kor+eng)
            
        Returns:
            분석 결과 딕셔너리
        """
        response = requests.post(
            f"{self.server_url}/analyze/ocr/from_path",
            params={'image_path': image_path, 'lang': lang}
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_directory(self, directory_path: str, lang: str = "eng", 
                          extensions: List[str] = ["jpg", "jpeg", "png", "tiff", "bmp"]) -> Dict[str, Any]:
        """
        디렉토리에 있는 모든 이미지 분석
        
        Args:
            directory_path: 서버에 있는 이미지 디렉토리 경로
            lang: OCR 언어 (기본값: eng, 한국어: kor, 한국어+영어: kor+eng)
            extensions: 처리할 이미지 파일 확장자 목록
            
        Returns:
            분석 결과 딕셔너리 목록
        """
        response = requests.post(
            f"{self.server_url}/analyze/ocr/directory",
            params={
                'directory_path': directory_path, 
                'lang': lang,
                'extensions': extensions
            }
        )
        response.raise_for_status()
        return response.json()

def save_results(results: Dict[str, Any], output_file: str):
    """분석 결과를 JSON 파일로 저장"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"결과가 {output_file}에 저장되었습니다.")

def main():
    parser = argparse.ArgumentParser(description='PDF 이미지 분석 클라이언트')
    parser.add_argument('--server', default='http://localhost:5000', help='이미지 분석 서버 URL')
    
    subparsers = parser.add_subparsers(dest='command', help='명령')
    
    # 단일 이미지 분석
    single_parser = subparsers.add_parser('analyze', help='단일 이미지 분석')
    single_parser.add_argument('image_path', help='이미지 파일 경로')
    single_parser.add_argument('--lang', default='eng', help='OCR 언어 (기본값: eng, 한국어: kor)')
    single_parser.add_argument('--output', help='결과를 저장할 JSON 파일 경로')
    
    # 여러 이미지 일괄 분석
    batch_parser = subparsers.add_parser('batch', help='여러 이미지 일괄 분석')
    batch_parser.add_argument('image_paths', nargs='+', help='이미지 파일 경로 목록')
    batch_parser.add_argument('--lang', default='eng', help='OCR 언어 (기본값: eng, 한국어: kor)')
    batch_parser.add_argument('--output', help='결과를 저장할 JSON 파일 경로')
    
    # 서버 경로로 분석
    path_parser = subparsers.add_parser('from_path', help='서버에 있는 이미지 경로로 분석')
    path_parser.add_argument('server_image_path', help='서버에 있는 이미지 파일 경로')
    path_parser.add_argument('--lang', default='eng', help='OCR 언어 (기본값: eng, 한국어: kor)')
    path_parser.add_argument('--output', help='결과를 저장할 JSON 파일 경로')
    
    # 디렉토리 분석
    dir_parser = subparsers.add_parser('directory', help='디렉토리에 있는 모든 이미지 분석')
    dir_parser.add_argument('directory_path', help='서버에 있는 이미지 디렉토리 경로')
    dir_parser.add_argument('--lang', default='eng', help='OCR 언어 (기본값: eng, 한국어: kor)')
    dir_parser.add_argument('--output', help='결과를 저장할 JSON 파일 경로')
    
    # 서버 상태 확인
    subparsers.add_parser('health', help='서버 상태 확인')
    
    args = parser.parse_args()
    
    client = ImageAnalysisClient(server_url=args.server)
    
    try:
        if args.command == 'analyze':
            results = client.analyze_image(args.image_path, args.lang)
            if args.output:
                save_results(results, args.output)
            else:
                print(json.dumps(results, ensure_ascii=False, indent=2))
                
        elif args.command == 'batch':
            results = client.analyze_images_batch(args.image_paths, args.lang)
            if args.output:
                save_results(results, args.output)
            else:
                print(json.dumps(results, ensure_ascii=False, indent=2))
                
        elif args.command == 'from_path':
            results = client.analyze_from_path(args.server_image_path, args.lang)
            if args.output:
                save_results(results, args.output)
            else:
                print(json.dumps(results, ensure_ascii=False, indent=2))
                
        elif args.command == 'directory':
            results = client.analyze_directory(args.directory_path, args.lang)
            if args.output:
                save_results(results, args.output)
            else:
                print(json.dumps(results, ensure_ascii=False, indent=2))
                
        elif args.command == 'health' or args.command is None:
            results = client.check_server_health()
            print(f"서버 상태: {results}")
            
    except requests.exceptions.ConnectionError:
        print(f"오류: 서버 연결 실패. 서버가 {args.server}에서 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"오류: {str(e)}")

if __name__ == "__main__":
    main()
