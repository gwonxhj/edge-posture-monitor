# Documentation Overview

본 디렉토리는 Edge AI Posture Monitoring System의 설계 및 동작 구조를 설명하는 문서들로 구성되어 있습니다.

## Core Documents

- system_architecture.md  
  → 전체 시스템 구조 및 구성 요소 설명

- runtime_sequence.md  
  → UART 기반 측정 흐름 및 상태 전이 과정 설명

- posture_detection_logic.md  
  → 자세 판단을 위한 feature 및 규칙 기반 로직 설명

- database_schema.md  
  → SQLite 기반 데이터 저장 구조 및 테이블 관계

- api_spec.md  
  → 모바일 앱과의 HTTP / WebSocket 인터페이스 명세

## Notes

본 문서들은 실제 구현 코드 기준으로 작성되었으며,
Mock Validation 및 Real Hardware Integration 단계 모두를 반영합니다.