# neuromeka_vfm

클라이언트 PC에서 Segmentation (SAM2, Grounding DINO), Pose Estimation (NVIDIA FoundationPose) 서버(RPC, ZeroMQ)와 통신하고, SSH/SFTP로 호스트에 mesh를 업로드하는 간단한 유틸 패키지입니다.

- Website: http://www.neuromeka.com
- Source code: https://github.com/neuromeka-robotics/neuromeka_vfm
- PyPI package: https://pypi.org/project/neuromeka_vfm/
- Documents: https://docs.neuromeka.com

## Web UI (VFM Tester)를 통해 사용 가능

- VFM Tester (Web UI): https://gitlab.com/neuromeka-group/nrmkq/nrmk_vfm_tester


## Installation
```bash
pip install neuromeka_vfm
```

## Python API (예제로 보는 사용법)

* 내 PC: 어플리케이션을 구현하고 이 패키지 (neuromeka_vfm)이 설치된 PC
* 서버PC (Host): Segmentation, Pose Estimation 도커 서버가 설치된 PC. 내 PC에 도커를 설치할 경우 localhost 사용.

### Segmentation
```python
from neuromeka_vfm import Segmentation

seg = Segmentation(
    hostname="192.168.10.63", 
    port=5432,
    compression_strategy="png",    # none | png | jpeg | h264
)

# Image Prompt를 이용한 등록
seg.add_image_prompt("drug_box", ref_rgb)
seg.register_first_frame(frame=first_rgb, 
                        prompt="drug_box", # ID str
                        use_image_prompt=True)

# Text Prompt를 이용한 등록
seg.register_first_frame(frame=first_rgb, 
                        prompt="box .",   # Text prompt (끝에 띄어쓰기 . 필수)
                        use_image_prompt=False)

# 등록된 mask에 대한 SAM2 tracking
resp = seg.get_next(next_rgb)
if isinstance(resp, dict) and resp.get("result") == "ERROR":
    print(f"Tracking error: {resp.get('message')}")
    seg.reset()
else:
    masks = resp

# Segmentation 설정/모델 선택 (nrmk_realtime_segmentation v0.2+)
caps = seg.get_capabilities()["data"]
current = seg.get_config()["data"]
seg.set_config(
    {
        "grounding_dino": {
            "backbone": "Swin-B",        # Swin-T | Swin-B
            "box_threshold": 0.35,
            "text_threshold": 0.25,
        },
        "dino_detection": {
            "threshold": 0.5,
            "target_multiplier": 25,
            "img_multiplier": 50,
            "background_threshold": -1.0,
            "final_erosion_count": 10,
            "segment_min_size": 20,
        },
        "sam2": {
            "model": "facebook/sam2.1-hiera-large",
            "use_legacy": False,
            "compile": False,
            "offload_state_to_cpu": False,
            "offload_video_to_cpu": False,
        },
    }
)

# SAM2 object 제거 (v0.2+, use_legacy=False에서만 지원)
seg.remove_object("cup_0")


seg.close()
```

#### Segmentation v0.2 설정 요약 (defaults/choices)
`seg.get_capabilities()` 결과는 서버 설정에 따라 달라질 수 있습니다. 아래는 v0.2 기본값입니다.
```yaml
grounding_dino:
  backbone:
    choices:
      - Swin-B
      - Swin-T
    default: Swin-T
  box_threshold:
    default: 0.35
    min: 0.0
    max: 1.0
  text_threshold:
    default: 0.25
    min: 0.0
    max: 1.0

dino_detection:
  threshold:
    default: 0.5
  target_multiplier:
    default: 25
  img_multiplier:
    default: 50
  background_threshold:
    default: -1.0
  final_erosion_count:
    default: 10
  segment_min_size:
    default: 20

sam2:
  model:
    choices:
      - facebook/sam2-hiera-base-plus
      - facebook/sam2-hiera-large
      - facebook/sam2-hiera-small
      - facebook/sam2-hiera-tiny
      - facebook/sam2.1-hiera-base-plus
      - facebook/sam2.1-hiera-large
      - facebook/sam2.1-hiera-small
      - facebook/sam2.1-hiera-tiny
    default: facebook/sam2.1-hiera-large
  use_legacy:
    default: false
  compile:
    default: false
  offload_state_to_cpu:
    default: false
  offload_video_to_cpu:
    default: false
```

#### Segmentation v0.2 주의사항/변경사항
- SAM2 VRAM 추정 실패 시 `seg.get_next()`가 `{"result":"ERROR"}`로 반환될 수 있으니 에러 처리 후 `reset`/재등록을 권장합니다.
- SAM2 `compile=True`는 첫 프레임 등록 및 `reset`이 느려질 수 있습니다.
- SAM2 CPU offloading은 `offload_state_to_cpu=True`와 `offload_video_to_cpu=True`를 함께 설정할 때 효과가 큽니다(legacy 모드에서는 `offload_video_to_cpu` 미지원).
- SAM2 `remove_object`는 `use_legacy=False`에서만 지원됩니다.
- GroundingDINO는 Swin-B 백본이 추가되었고, 프롬프트 토큰 병합 이슈가 수정되었습니다.

### Pose Estimation

**Mesh 파일 업로드**: 등록/인식하고자 하는 mesh 파일 (stl)을 호스트PC의 '/opt/meshes/' 경로에 업로드 (직접 SSH 통해 파일을 옮겨도 됨)
```python
from neuromeka_vfm import upload_mesh
upload_mesh(
    host="192.168.10.63",
    user="user",
    password="pass",                  
    local="mesh/my_mesh.stl",         # 내 PC mesh 경로
    remote="/opt/meshes/my_mesh.stl", # 호스트PC mesh 경로 (도커 볼륨마운트)
)
```

초기화
```python
from neuromeka_vfm import PoseEstimation

pose = PoseEstimation(host="192.168.10.72", port=5557)  

pose.init(
    mesh_path="/app/modules/foundation_pose/mesh/my_mesh.stl",
    apply_scale=1.0,  
    track_refine_iter=3,
    min_n_views=40,
    inplane_step=60
)
```
- mesh_path: 사용할 물체 메시 파일(STL/OBJ 등) 경로. 없으면 초기화 실패.
- apply_scale: 메시를 로드한 뒤 전체를 배율 조정하는 스케일 값. 단위 없는 곱셈 계수.
    - STL 모델이 미터 단위라면 1.0 (스케일 없음)
    - STL 모델이 센티미터 단위라면 0.01 (1 cm → 0.01 m)
    - STL 모델이 밀리미터 단위라면 0.001 (1 mm → 0.001 m)
- force_apply_color: True일 때 메시에 단색 텍스처를 강제로 입힘. 메시가 색상을 안 가졌을 때 시각화 안정성을 위해 사용.
- apply_color: force_apply_color가 True일 때 적용할 RGB 색상값(0~255) 튜플.
- est_refine_iter: 초기 등록(register) 단계에서 포즈를 반복 정련하는 횟수. 값이 클수록 정확도 ↑, 연산 시간 ↑.
- track_refine_iter: 추적(track) 단계에서 한 프레임당 포즈 정련 반복 횟수.
- min_n_views: 초기 뷰 샘플링 시 생성할 최소 카메라 뷰 수(회전 후보 수에 영향).
- inplane_step: in-plane 회전 샘플링 간격(도 단위). 값이 작을수록 더 많은 회전 후보를 생성.


인식 및 추적
```python
# 초기 등록 (iteration 생략 시 서버 기본값, check_vram=True로 VRAM 사전 체크)
register_resp = pose.register(rgb=rgb0, depth=depth0, mask=mask0, K=cam_K, check_vram=True)

# 추적 (bbox_xywh로 탐색 범위 제한 가능)
track_resp = pose.track(rgb=rgb1, depth=depth1, K=cam_K, bbox_xywh=bbox_xywh)
pose.close()
```
- cam_K: camera intrinsic
- RGB resolution이 크거나, min_n_views 값이 크거나, inplane_step이 작을 경우 GPU VRAM 초과 에러 발생. 
- register check_vram=True 일 경우 VRAM 초과 사전 검사하여 shutdown 방지.


## VFM (Vision Foundation Model) latency benchmark
로컬 서버 구동 시 측정. 빈칸은 아직 미측정 항목입니다. 

**RTX 5060**
| Task | Prompt | None (s) | JPEG (s) | PNG (s) | h264 (s) |
| --- | --- | --- | --- | --- | --- |
| Grounding DINO | text (human . cup .) | 0.86 | 0.35 | 0.50 | 0.52 |
| DINOv2 | image prompt | 0.85 | 0.49 | 0.65 | 0.63 |
| SAM2 | - |  |  |  |  |
| FoundationPose registration | - |  |  |  |  |
| FoundationPose track | - |  |  |  |  |

**RTX 5090**
| Task | Prompt | None (s) | JPEG (s) | PNG (s) | h264 (s) |
| --- | --- | --- | --- | --- | --- |
| Grounding DINO | text (human . cup .) |  |  |  |  |
| DINOv2 | image prompt |  |  |  |  |
| SAM2 | - |  |  |  |  |
| FoundationPose registration | - | 0.4 | - |  |  |
| FoundationPose track | - | 0.03 |  |  |  |

**Jetson Orin**
| Task | Prompt | None (s) | JPEG (s) | PNG (s) | h264 (s) |
| --- | --- | --- | --- | --- | --- |
| Grounding DINO | text (human . cup .) |  |  |  |  |
| DINOv2 | image prompt |  |  |  |  |
| SAM2 | - |  |  |  |  |
| FoundationPose registration | - | 0.4 | - |  |  |
| FoundationPose track | - | 0.03 |  |  |  |

## 릴리스 노트
- 0.1.2: Segmentation 응답 성공 판정 개선(`result`/`success`/`status` 모두 지원), image prompt 등록/사용 오류 수정, PoseEstimation `register`에 `check_vram` 옵션 반영.
- 0.1.1: PoseEstimation/Segmentation에서 리소스 정리 개선, iteration 미전달 시 서버 기본값 사용, pose 데모 예제 추가.
- 0.1.0: 초기 공개 버전. FoundationPose RPC 클라이언트, 실시간 세그멘테이션 클라이언트, SSH 기반 mesh 업로드 CLI/API 포함.
