# Claude Code용 가이드: 기존 영상/사진 기반 크루즈 여행 숏폼을 Remotion으로 만드는 법

작성일: 2026-03-11  
대상: `video-factory` 코드베이스를 바로 수정해서 크루즈 여행 숏폼을 만들 사람  
전제: 강의형 영상이 아니라, 실제 여행 영상/사진/자막/효과/시각자료가 많은 세로형 숏폼 제작자

---

## 0. 이 문서의 목적

이 문서는 아래 4가지를 한 번에 해결하기 위한 실전 가이드다.

1. 현재 `video-factory` 코드베이스로 **당장 가능한 것**
2. 크루즈 여행 숏폼에 맞게 **추가 구현해야 할 것**
3. Claude Code가 바로 작업할 수 있게 **복붙 가능한 코드 구조와 구현 순서**
4. 나중에 이 작업을 반복 자동화하기 위한 **Skill 패키징 방법**

중요:
- 이 문서에는 API 키, 시크릿, 로그인 정보는 넣지 않는다.
- 모든 예시는 `환경변수` 또는 `placeholder` 기준으로 쓴다.
- 지금 코드베이스는 원래 데이터/교육형 설명 영상에 강하다.  
  크루즈 숏폼에 맞추려면 **"사진/영상 자산 우선" 구조**로 일부 장면 타입을 새로 추가해야 한다.

---

## 1. 현재 코드베이스로 이미 가능한 것

### 1-1. 지금 바로 쓸 수 있는 핵심 구조

현재 `video-factory`는 아래 흐름으로 움직인다.

```text
script.json
  -> audioConfig.json
  -> props.json
  -> VideoComposition.tsx
  -> Remotion render
```

관련 파일:
- 개요 문서: [00-overview.md](/Users/elon/Documents/elon_youtube/video-factory/docs/00-overview.md)
- 장면 가이드: [04-scene-guide.md](/Users/elon/Documents/elon_youtube/video-factory/docs/04-scene-guide.md)
- 고급 시각화 리서치: [07-advanced-visual-components.md](/Users/elon/Documents/elon_youtube/video-factory/docs/07-advanced-visual-components.md)
- 장면 등록 스위치: [VideoComposition.tsx](/Users/elon/Documents/elon_youtube/video-factory/src/VideoComposition.tsx#L56)
- 타입 정의: [types.ts](/Users/elon/Documents/elon_youtube/video-factory/src/types.ts#L1)

### 1-2. 지금 있는 장면 타입

이미 있는 장면 타입은 생각보다 많다.

- 기본 설명형:
  - `intro`
  - `content`
  - `quote`
  - `outro`
- 비교/정보 정리형:
  - `compare`
  - `comparison-table`
  - `pros-cons`
  - `before-after`
- 구조/일정/프로세스형:
  - `timeline`
  - `steps`
  - `roadmap`
  - `kanban`
  - `cycle`
  - `flowchart`
- 데이터 시각화형:
  - `bar-chart`
  - `line-chart`
  - `pie-chart`
  - `bubble-chart`
  - `heatmap`
  - `dashboard`
  - `stat-counter`
  - `number-highlight`
  - `gauge`
  - `radar`
- 레이아웃/카드형:
  - `feature-cards`
  - `profile-card`
  - `icon-grid`
  - `scoreboard`
  - `mind-map`
  - `matrix-2x2`
  - `tier-list`

### 1-3. 현재 코드베이스가 크루즈 숏폼에 특히 유리한 점

1. **자막 동기화 구조가 이미 있다**
   - `audioConfig.json`의 `cues`, `visualTriggers`를 이용해
   - 자막, 포인트 텍스트, 카드 등장 타이밍을 프레임 단위로 맞출 수 있다.

2. **배경/데코레이션이 이미 풍부하다**
   - 다만 지금은 테크/네온 톤이 기본이라
   - 크루즈 전용 테마를 하나 더 추가하는 것이 좋다.

3. **TransitionSeries 구조가 이미 있다**
   - 장면 전환을 Remotion 방식으로 통제하고 있어
   - 짧은 숏폼에서 리듬감 있는 컷 편집을 만들기 좋다.

4. **정보를 시각화하는 컴포넌트가 많다**
   - 크루즈 비용 비교
   - 선실 비교
   - 하루 일정
   - 배 내 시설 요약
   - 기항지 추천
   같은 내용을 영상화하기 좋다.

### 1-4. 현재 코드베이스의 한계

지금 구조는 "설명형/데이터형 장면"에는 강하지만, 아래는 약하다.

1. **실제 영상 클립을 주인공으로 쓰는 scene가 없음**
2. **사진 몽타주/켄번즈/패럴랙스 전용 scene가 없음**
3. **세로형 여행 쇼츠 전용 safe area 체계가 없음**
4. **크루즈/여행 특화 시각언어가 없음**
   - 지도
   - 항로
   - 날짜/기항지
   - 날씨/파도/시간대
   - 가격/혜택 카드
5. **후킹용 숏폼 자막 스타일이 약함**
   - 현재 `SyncSubtitleBar`는 설명형엔 좋지만
   - 여행 쇼츠용 "짧고 세게" 자막 스타일은 따로 만드는 게 좋다.

결론:
- **지금 있는 구조는 버릴 필요 없다**
- 대신 **미디어 자산 중심 장면 3~4개만 새로 추가**하면 크루즈 숏폼에도 바로 쓸 수 있다.

---

## 2. 크루즈 여행 숏폼에 맞는 추천 아키텍처

### 2-1. 가장 추천하는 방향

강의형 영상처럼 `텍스트 -> 차트 -> 설명` 순으로 가면 안 된다.  
크루즈 숏폼은 아래 순서가 맞다.

```text
실제 영상/사진 훅
-> 강한 자막
-> 1~2개의 핵심 정보 카드
-> 다음 컷으로 빠르게 전환
-> 마지막 CTA
```

### 2-2. 추천 장면 타입 구성

크루즈 숏폼용으로는 아래 6개면 충분하다.

1. `media-broll`
   - mp4 중심
   - 실제 배, 객실, 바다, 수영장, 뷔페 영상

2. `photo-kenburns`
   - jpg/png/webp 중심
   - 객실, 선상뷰, 음식, 갑판, 기항지 사진

3. `captioned-hook`
   - 화면 가득 짧은 자막
   - "이 크루즈 진짜 미쳤다", "하루 20만원대로 가능", "이 선실은 무조건 피해라"

4. `route-itinerary`
   - 지도 대신 심플 타임라인/기항지 카드
   - 출항 -> 바다 위 -> 기항지1 -> 기항지2 -> 귀항

5. `price-breakdown`
   - 비용, 포함/불포함, 가성비 비교

6. `review-card`
   - 장단점 3개
   - 추천 대상/비추천 대상

### 2-3. 숏폼 포맷 예시

#### 포맷 A. 감성형
- 0~2초: 선상/바다/야경 훅
- 2~6초: 객실/수영장/공연 컷 교차
- 6~10초: 핵심 한 줄
- 10~18초: 장점 2~3개
- 18~24초: 가격/팁
- 24~30초: 저장/팔로우 CTA

#### 포맷 B. 정보형
- 0~2초: "이 크루즈 얼마였냐면"
- 2~6초: 가격 카드
- 6~12초: 객실/식사/기항지
- 12~18초: 추천 대상
- 18~24초: 비추천 대상
- 24~30초: 저장 CTA

#### 포맷 C. 후기형
- 0~2초: "좋았던 점 3개 / 별로였던 점 2개"
- 2~12초: 좋았던 점
- 12~20초: 별로였던 점
- 20~28초: 총평

---

## 3. 파일/폴더 설계 권장안

### 3-1. 프로젝트 폴더 구조

크루즈 숏폼 프로젝트는 아래처럼 두는 게 좋다.

```text
projects/cruise-short-001/
  script.json
  audioConfig.json
  props.json
  media/
    videos/
      hook.mp4
      pool.mp4
      dinner.mp4
    photos/
      cabin-01.jpg
      deck-01.jpg
      buffet-01.jpg
    overlays/
      logo.png
      sticker-save.png
      route-map.png
  output/
    video.mp4
    thumbnail.png
```

### 3-2. asset 명명 규칙

- `hook-01.mp4`
- `cabin-balcony-01.jpg`
- `port-osaka-01.jpg`
- `dining-buffet-01.jpg`
- `overlay-price-card.png`

좋은 이유:
- Claude Code가 파일 의미를 추론하기 쉽다.
- 나중에 manifest 자동화할 때 유리하다.

---

## 4. 구현 전략: 현재 코드베이스에 무엇을 추가하면 되나

### 4-1. 가장 먼저 추가할 SceneType

`src/types.ts`의 `SceneType`에 아래를 추가하는 것을 추천한다.

```ts
export type SceneType =
  | "intro"
  | "content"
  | "code"
  | "diagram"
  | "outro"
  | "compare"
  | "steps"
  | "stats"
  | "quote"
  | "timeline"
  | "highlight"
  | "checklist"
  | "icon-grid"
  | "funnel"
  | "gauge"
  | "pyramid"
  | "feature-cards"
  | "radar"
  | "venn"
  | "matrix-2x2"
  | "flowchart"
  | "cycle"
  | "line-chart"
  | "before-after"
  | "tier-list"
  | "scoreboard"
  | "mind-map"
  | "swot"
  | "kanban"
  | "roadmap"
  | "pie-chart"
  | "bubble-chart"
  | "sankey"
  | "pros-cons"
  | "dashboard"
  | "bar-chart"
  | "heatmap"
  | "comparison-table"
  | "stat-counter"
  | "profile-card"
  | "progress-tracker"
  | "rating-display"
  | "number-highlight"
  | "media-broll"
  | "photo-kenburns"
  | "captioned-hook"
  | "route-itinerary"
  | "price-breakdown"
  | "review-card";
```

### 4-2. `SceneVisual`에 추가할 필드

```ts
export interface MediaClip {
  src: string;
  startFrom?: number;
  endAt?: number;
  muted?: boolean;
  playbackRate?: number;
}

export interface PhotoAsset {
  src: string;
  caption?: string;
  focusX?: number;
  focusY?: number;
}

export interface RouteStop {
  day: string;
  title: string;
  subtitle?: string;
}

export interface PriceLine {
  label: string;
  value: string;
  highlight?: boolean;
}

export interface ReviewPoint {
  text: string;
  tone: "pro" | "con" | "tip";
}
```

`SceneVisual` 안에:

```ts
mediaClip?: MediaClip;
photoAssets?: PhotoAsset[];
routeStops?: RouteStop[];
priceLines?: PriceLine[];
reviewPoints?: ReviewPoint[];
badgeText?: string;
```

---

## 5. 가장 중요한 장면 2개: 바로 구현 가능한 코드 예시

### 5-1. `MediaBrollScene.tsx`

용도:
- 기존 mp4 영상 위에
- 제목, 짧은 자막, 배지, CTA를 얹는 장면

```tsx
import React from "react";
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from "remotion";
import type { Scene, Theme, NarrationCue, VisualTrigger } from "../types";
import { SyncSubtitleBar } from "../components/SyncSubtitleBar";

interface Props {
  scene: Scene;
  theme: Theme;
  durationInFrames: number;
  cues: NarrationCue[];
  triggers: VisualTrigger[];
}

export const MediaBrollScene: React.FC<Props> = ({
  scene,
  theme,
  durationInFrames,
  cues,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame, fps, durationInFrames: 20 });
  const titleY = interpolate(progress, [0, 1], [40, 0]);
  const titleOpacity = interpolate(progress, [0, 1], [0, 1]);

  const clip = scene.visual.mediaClip;
  if (!clip) {
    return <AbsoluteFill style={{ backgroundColor: "#000" }} />;
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <OffthreadVideo
        src={staticFile(clip.src)}
        startFrom={clip.startFrom ?? 0}
        endAt={clip.endAt}
        muted={clip.muted ?? true}
        playbackRate={clip.playbackRate ?? 1}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />

      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0.25) 35%, rgba(0,0,0,0.05) 100%)",
        }}
      />

      {scene.visual.badgeText ? (
        <div
          style={{
            position: "absolute",
            top: 120,
            left: 48,
            padding: "10px 18px",
            borderRadius: 999,
            backgroundColor: "rgba(255,255,255,0.14)",
            color: "#fff",
            fontSize: 30,
            fontWeight: 700,
            backdropFilter: "blur(12px)",
          }}
        >
          {scene.visual.badgeText}
        </div>
      ) : null}

      <div
        style={{
          position: "absolute",
          left: 48,
          right: 48,
          bottom: 220,
          transform: `translateY(${titleY}px)`,
          opacity: titleOpacity,
        }}
      >
        <div
          style={{
            color: "#fff",
            fontSize: 70,
            fontWeight: 900,
            lineHeight: 1.06,
            letterSpacing: -2,
            textShadow: "0 8px 24px rgba(0,0,0,0.45)",
          }}
        >
          {scene.visual.headline}
        </div>

        {scene.displayText ? (
          <div
            style={{
              marginTop: 18,
              color: "rgba(255,255,255,0.92)",
              fontSize: 34,
              fontWeight: 600,
              lineHeight: 1.35,
            }}
          >
            {scene.displayText}
          </div>
        ) : null}
      </div>

      <SyncSubtitleBar
        cues={cues}
        color="#ffffff"
        activeColor={theme.colors.primary}
      />
    </AbsoluteFill>
  );
};
```

언제 쓰면 좋은가:
- 출항 뷰
- 바다/수영장/공연 B-roll
- 객실 투어
- 음식 몽타주

### 5-2. `PhotoKenBurnsScene.tsx`

용도:
- 사진 여러 장을
- 줌/패닝/겹침으로 세련되게 보여주는 장면

```tsx
import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Scene, Theme, NarrationCue, VisualTrigger } from "../types";
import { SyncSubtitleBar } from "../components/SyncSubtitleBar";

interface Props {
  scene: Scene;
  theme: Theme;
  durationInFrames: number;
  cues: NarrationCue[];
  triggers: VisualTrigger[];
}

export const PhotoKenBurnsScene: React.FC<Props> = ({
  scene,
  durationInFrames,
  cues,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const photos = scene.visual.photoAssets ?? [];

  return (
    <AbsoluteFill style={{ backgroundColor: "#081018" }}>
      {photos.map((photo, index) => {
        const localFrame = frame - index * Math.floor(durationInFrames / Math.max(photos.length, 1));
        const appear = spring({
          frame: localFrame,
          fps,
          durationInFrames: 18,
        });

        const scale = interpolate(localFrame, [0, 80], [1, 1.12], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const translateX = interpolate(localFrame, [0, 80], [0, -40], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={photo.src}
            style={{
              position: "absolute",
              inset: 0,
              opacity: appear,
              transform: `scale(${scale}) translateX(${translateX}px)`,
            }}
          >
            <Img
              src={staticFile(photo.src)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
            />
          </div>
        );
      })}

      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.08) 60%, rgba(0,0,0,0.28) 100%)",
        }}
      />

      <div
        style={{
          position: "absolute",
          left: 44,
          right: 44,
          bottom: 210,
          color: "#fff",
        }}
      >
        <div
          style={{
            fontSize: 68,
            fontWeight: 900,
            lineHeight: 1.06,
            letterSpacing: -1.8,
          }}
        >
          {scene.visual.headline}
        </div>
      </div>

      <SyncSubtitleBar cues={cues} color="#fff" activeColor="#ffd38a" />
    </AbsoluteFill>
  );
};
```

언제 쓰면 좋은가:
- 객실 사진 3장 비교
- 음식/디저트/라운지 포토 컷
- 기항지 풍경 컷

---

## 6. `VideoComposition.tsx` 등록 방법

새 장면을 추가하면 [VideoComposition.tsx](/Users/elon/Documents/elon_youtube/video-factory/src/VideoComposition.tsx#L56) 에 import와 case를 넣어야 한다.

예시:

```tsx
import { MediaBrollScene } from "./scenes/MediaBrollScene";
import { PhotoKenBurnsScene } from "./scenes/PhotoKenBurnsScene";
```

그리고 switch에:

```tsx
case "media-broll":
  return (
    <MediaBrollScene
      scene={scene}
      theme={theme}
      durationInFrames={durationInFrames}
      cues={cues}
      triggers={triggers}
    />
  );

case "photo-kenburns":
  return (
    <PhotoKenBurnsScene
      scene={scene}
      theme={theme}
      durationInFrames={durationInFrames}
      cues={cues}
      triggers={triggers}
    />
  );
```

---

## 7. 크루즈 여행 숏폼용 자막 전략

### 7-1. 현재 코드베이스에서 바로 가능한 방식

현재는 `audioConfig.json`의 `cues` 기반으로 `SyncSubtitleBar`를 쓰는 방식이다.

장점:
- 기존 구조와 잘 맞음
- 타이밍 정밀도 높음
- 설명형/후기형에 안정적

단점:
- 틱톡/릴스 스타일의 단어별 팝업 자막에는 약함

### 7-2. 지금 바로 추천하는 자막 스타일 3개

1. **하단 안정형**
   - 여행 후기/정보 요약용
   - 가장 안전

2. **중앙 펀치형**
   - "이거 진짜 미쳤다"
   - "이 가격 실화냐"
   - 후킹용

3. **상단 배지 + 하단 본문형**
   - 상단: `DAY 2 / 오사카`
   - 하단: 본문 자막

### 7-3. 조사하면 좋은 Remotion 공식 기능

Remotion 공식 문서 기준으로 꼭 볼 것:
- `OffthreadVideo`
  - https://www.remotion.dev/docs/offthreadvideo
- `Img`
  - https://www.remotion.dev/docs/img
- `staticFile`
  - https://www.remotion.dev/docs/staticfile
- `Sequence`
  - https://www.remotion.dev/docs/sequence
- `spring`
  - https://www.remotion.dev/docs/spring
- `interpolate`
  - https://www.remotion.dev/docs/interpolate
- `TransitionSeries`
  - https://www.remotion.dev/docs/transitions/transitionseries
- `@remotion/captions`
  - `parseSrt`: https://www.remotion.dev/docs/captions/parse-srt
  - `createTikTokStyleCaptions`: https://www.remotion.dev/docs/captions/create-tiktok-style-captions

실무 해석:
- **지금 코드베이스엔 `SyncSubtitleBar` 유지**
- **틱톡 스타일은 2차 구현으로 `@remotion/captions` 연구**

---

## 8. 크루즈 숏폼에 바로 먹히는 시각화 아이디어 30개

### 8-1. 훅용

1. 출항 직후 배 측면 와이드 + 대형 한 줄
2. 선상 야경 + 골드 배지
3. 객실 문 열리며 바다 뷰 reveal
4. 음식 close-up 3컷 빠른 교차
5. 수영장 + 공연 + 야경 3분할

### 8-2. 정보형

6. "총 비용" number-highlight
7. 선실 등급 comparison-table
8. 포함/불포함 pros-cons
9. 하루 일정 timeline
10. 기항지별 route-itinerary
11. 배 안 시설 icon-grid
12. 크루즈 선택 기준 checklist

### 8-3. 후기형

13. 좋았던 점 3개 steps
14. 아쉬웠던 점 2개 pros-cons
15. 추천 대상 / 비추천 대상 compare
16. 재방문 의사 scoreboard
17. 총평 quote

### 8-4. 감성형

18. 포토 스택 collage
19. Day 1 -> Day 4 photo-kenburns
20. 해질녘 -> 밤 전환 montage
21. 비 오는 날 / 맑은 날 before-after
22. 객실 inside / balcony split-screen

### 8-5. 판매형

23. 얼리버드 가격 카드
24. "이 가격대면 무조건 발코니" compare
25. 선실 업그레이드 추천 matrix
26. 크루즈 vs 호텔+항공 price-breakdown
27. honeymoon / family / parents segment compare

### 8-6. CTA형

28. 저장해두고 나중에 보기 badge
29. 다음 편 예고 card
30. "오사카 기항지 편도 만들까요?" 댓글 CTA

---

## 9. 조사 우선순위

### 9-1. 지금 당장 조사할 것

1. Remotion에서 `OffthreadVideo` 기반 세로형 숏폼 렌더 안정성
2. `@remotion/captions` 기반 단어별 자막 스타일
3. 세로형 safe area와 자막 가독성
4. travel montage에서 장면 길이 패턴
5. Ken Burns/Parallax가 과하면 촌스러워지는 기준

### 9-2. 그 다음 조사할 것

1. 지도 route animation
   - 직접 SVG 경로 애니메이션
   - 또는 정적 지도 이미지 + 경로 overlay
2. LUT/색보정 전처리
   - ffmpeg 전처리로 영상 톤 통일
3. 배경 음악 비트 컷
4. 여행 후기용 리뷰 카드 템플릿
5. 호텔/크루즈 가격 비교 레이아웃

### 9-3. 나중에 조사할 것

1. 프레임 기반 auto highlight
2. OCR 기반 자동 자막 위치 회피
3. 댓글 기반 후속 영상 자동 기획
4. 항로/날씨/시간대 데이터 자동 overlay

---

## 10. Claude Code에게 바로 시킬 수 있는 작업 순서

### Phase 1. 최소 구현

1. `SceneType` 확장
2. `SceneVisual`에 media/photo 관련 필드 추가
3. `MediaBrollScene.tsx` 생성
4. `PhotoKenBurnsScene.tsx` 생성
5. `VideoComposition.tsx`에 case 추가
6. 샘플 프로젝트 `projects/cruise-short-001` 생성

### Phase 2. 크루즈 특화

7. `RouteItineraryScene.tsx`
8. `PriceBreakdownScene.tsx`
9. `ReviewCardScene.tsx`
10. 크루즈 전용 theme 추가

### Phase 3. 자막/효과 고도화

11. 후킹 자막 컴포넌트 추가
12. 사진/영상 전환용 preset 제작
13. caption style variant 3종 추가

---

## 11. Claude Code용 복붙 프롬프트

### 프롬프트 1. media-broll scene 추가

```text
video-factory 코드베이스에서 크루즈 여행 숏폼용 media-broll scene을 추가해.

조건:
- 기존 mp4 파일을 OffthreadVideo로 재생
- 상단 badge, 하단 headline, 하단 보조 자막 지원
- 세로형 1080x1920 숏폼 기준
- SceneType, SceneVisual, VideoComposition.tsx 등록까지 같이 수정
- 기존 remotion 스타일(useCurrentFrame, spring, interpolate) 유지
```

### 프롬프트 2. photo-kenburns scene 추가

```text
video-factory에 사진 여러 장을 켄번즈 방식으로 보여주는 photo-kenburns scene을 추가해.

조건:
- Img 사용
- 확대/이동 애니메이션은 interpolate 기반
- 하단 자막과 headline 포함
- 여행/크루즈 감성에 맞는 미세한 움직임
```

### 프롬프트 3. cruise-short 샘플 프로젝트 생성

```text
projects/cruise-short-001 샘플 프로젝트를 만들어줘.

구성:
- hook 영상 1개
- cabin, buffet, deck 사진 3장
- 25~30초 분량
- scene 구성은 captioned-hook -> media-broll -> photo-kenburns -> price-breakdown -> outro
```

### 프롬프트 4. 크루즈 테마 추가

```text
video-factory에 cruise-luxury theme를 추가해.

요구:
- 바다/선셋/딥네이비/골드 기반
- 텍스트 가독성 우선
- 여행/럭셔리 느낌
- 기존 elon-business보다 덜 공격적이고 더 감성적인 톤
```

### 프롬프트 5. 숏폼용 자막 스타일 추가

```text
video-factory에 shorts-caption variant를 추가해.

요구:
- 세로형 safe area 고려
- 2줄 이내
- 단어 강조 색상 변경
- hook용 large caption과 body용 compact caption 모두 지원
```

---

## 12. Skill로 패키징하는 법

### 12-1. 추천 스킬 폴더 구조

```text
skills/cruise-shorts-remotion/
  SKILL.md
  templates/
    cruise-short-script-template.json
    cruise-shotlist-template.md
  references/
    remotion-links.md
    visual-ideas.md
  prompts/
    add-media-broll-scene.txt
    add-photo-kenburns-scene.txt
    create-cruise-project.txt
```

### 12-2. SKILL.md에 들어갈 핵심

- 트리거:
  - "크루즈 숏폼"
  - "여행 숏폼"
  - "기존 영상 사진으로 remotion"
  - "travel shortform"
- 프로젝트 경로:
  - `/Users/elon/Documents/elon_youtube/video-factory`
- 실행 순서:
  1. 프로젝트 asset 구조 확인
  2. 필요한 scene type 추가 여부 판단
  3. template로 `script.json` 초안 생성
  4. render

### 12-3. 왜 skill화가 유리한가

- 매번 같은 설명을 안 해도 된다
- shotlist -> script -> asset mapping이 반복 자동화된다
- 크루즈 말고 호텔/리조트/항공/투어 숏폼에도 확장 가능하다

---

## 13. 결론

이 코드베이스는 원래 교육형/데이터형 영상에 강하지만,  
크루즈 여행 숏폼으로 전환하는 데 필요한 핵심은 의외로 많지 않다.

정리하면:

1. **버릴 것 없음**
2. **media-broll / photo-kenburns / captioned-hook / price-breakdown 정도만 추가**
3. **자막 스타일만 숏폼 전용으로 개선**
4. **크루즈 전용 theme와 asset 규칙만 잡으면 바로 쓸 수 있음**

실무적으로는 아래 순서가 가장 좋다.

1. `media-broll`
2. `photo-kenburns`
3. `captioned-hook`
4. 샘플 프로젝트 1개
5. 이후 `route-itinerary`, `price-breakdown`, `review-card`

이 순서면 Claude Code가 바로 구현할 수 있고,  
나중에 그대로 skill로 패키징하는 것도 어렵지 않다.

---

## 14. 참고 링크

### 공식 Remotion 문서
- OffthreadVideo: https://www.remotion.dev/docs/offthreadvideo
- Img: https://www.remotion.dev/docs/img
- staticFile: https://www.remotion.dev/docs/staticfile
- Sequence: https://www.remotion.dev/docs/sequence
- spring: https://www.remotion.dev/docs/spring
- interpolate: https://www.remotion.dev/docs/interpolate
- TransitionSeries: https://www.remotion.dev/docs/transitions/transitionseries
- parseSrt: https://www.remotion.dev/docs/captions/parse-srt
- createTikTokStyleCaptions: https://www.remotion.dev/docs/captions/create-tiktok-style-captions

### 이 코드베이스에서 먼저 볼 파일
- [VideoComposition.tsx](/Users/elon/Documents/elon_youtube/video-factory/src/VideoComposition.tsx)
- [types.ts](/Users/elon/Documents/elon_youtube/video-factory/src/types.ts)
- [00-overview.md](/Users/elon/Documents/elon_youtube/video-factory/docs/00-overview.md)
- [04-scene-guide.md](/Users/elon/Documents/elon_youtube/video-factory/docs/04-scene-guide.md)
- [07-advanced-visual-components.md](/Users/elon/Documents/elon_youtube/video-factory/docs/07-advanced-visual-components.md)
