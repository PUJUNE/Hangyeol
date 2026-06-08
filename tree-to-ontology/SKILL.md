---
name: tree-to-ontology
description: 기존 markdown tree wiki를 온톨로지 구조로 업그레이드하는 스킬. related_axes 단일 부모 트리는 유지하고 ontology_level·ontology_role·entrypoint·typed_relations를 추가해 관계 타입과 방향을 명시. 트리거 — tree to ontology, tree to ontrology, 트리 온톨로지화, /tree-to-ontology.
---

# tree-to-ontology

트리 위키의 위치 구조를 보존하면서 의미 관계를 `typed_relations`로 분리하는 스킬. 트리는 "노드가 어디에 있는가"를 담당하고, 온톨로지는 "노드가 무엇과 어떤 관계인가"를 담당한다.

## 적용 기준

- 기존 위키가 `wiki/areas/`와 콘텐츠 카테고리를 가진 markdown 위키일 때 사용한다.
- 콘텐츠 노드가 `related_axes` 부모 1개를 이미 갖고 있으면 바로 전환한다.
- 다중 부모·본문 wikilink가 섞인 상태라면 먼저 트리 lint를 실행해 구조 오염 여부를 확인한다.
- 사용자가 관계 타입을 넓게 자동 생성하길 원하지 않으면, 확정된 관계만 넣고 나머지는 `belongs_to`만 부여한다.

## 전환 순서

1. 원본 `wiki/`를 날짜가 붙은 백업 폴더로 복사한다.
2. 현재 구조를 감사한다. 콘텐츠 노드는 `related_axes` 1개, 금지 파일 `index.md`·`log.md` 없음, 깨진 링크 없음이 기준이다.
3. 진입점 노드를 확정한다. 학습 위키라면 보통 theme 2~5개가 level 0이 된다.
4. 레벨을 부여한다. 기본값은 theme level 0, concept·synthesis·entity level 1, essay·source level 2이다.
5. 모든 콘텐츠 노드에 `belongs_to` relation을 넣고, 지도·축 노드에는 `has_axis`와 `part_of`를 넣는다.
6. 사용자가 제공한 관계 목록이나 본문에서 확인된 관계만 `causes`, `contradicts`, `grounds`, `supports`, `applies_to` 등으로 추가한다.
7. `scripts/ontology_audit.py`로 진입점, relation target, 허용 relation type, 부모 1개 규칙을 검증한다.

## Frontmatter 확장

```yaml
ontology_level: "1"
ontology_role: "core-concept"
entrypoint: false
typed_relations:
  - type: "belongs_to"
    target: "[[학습영역-주제축]]"
  - type: "shares_structure_with"
    target: "[[다른-노드]]"
```

## 기본 Relation Types

- 구조 관계: `belongs_to`, `part_of`, `has_axis`, `has_mechanism`
- 논리 관계: `causes`, `contradicts`, `addresses`, `pairs_with`, `extends`, `instantiates`, `applies_to`, `shares_structure_with`
- 근거 관계: `grounds`, `supports`, `evidenced_by`, `draws_from`

## 리소스

- `scripts/upgrade_tree_to_ontology.py` — 기존 위키 frontmatter에 온톨로지 필드를 추가.
- `scripts/ontology_audit.py` — relation target, 진입점, relation type, 부모 규칙 감사.
- `references/relation-types.md` — relation type 선택 기준.

## 주의

- 온톨로지화는 트리를 지우는 작업이 아니다. `related_axes`는 유지하고 `typed_relations`를 별도 의미 계층으로 추가한다.
- 관계 타입을 추측으로 많이 만들지 않는다. 명시 근거가 부족하면 `belongs_to`만 두고 관계 후보는 대화로 보고한다.
- 기존 `wiki/index.md`와 `wiki/log.md`는 자동 생성하지 않는다.
