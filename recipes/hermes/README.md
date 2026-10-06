# Hermes 설치 가이드

맥미니에서 검증 전

## 설치 순서

1. **저장소 복제 및 기본 설정**
   - `git clone`로 저장소를 복제한다.
   - `./setup --host cli claude`로 기본 설정을 완료한다.

2. **Superpowers 플러그인 설치**
   - `hermes plugins install obra/superpowers --enable`로 플러그인을 설치하고 활성화한다.

3. **Cron과 Telegram 설정 적용**
   - `cron.yaml`를 Hermes 설정에 적용한다.
   - `telegram-topics.yaml`를 `platforms.telegram.extra.dm_topics`에 적용한다.

4. **화이트리스트 설정**
   - `astack feed seed`로 화이트리스트를 설정한다.

5. **하루 사이클 확인**
   - 다음 시간대에 작업이 실행되는지 확인한다:
     - 05:00 (astack-feed)
     - 07:00 (astack-morning)
     - 20:00 (astack-dream)
     - 20:30 (astack-consolidate)
     - 21:00 (astack-ask-tonight)
     - 01:00 (astack-night)

## 되돌리기 순서

1. Telegram 설정 제거
2. Cron 작업 비활성화
3. Superpowers 플러그인 제거 (`hermes plugins uninstall obra/superpowers`)
4. astack 설치 되돌리기 (`./setup --uninstall --host cli claude`)
5. 저장소 제거
