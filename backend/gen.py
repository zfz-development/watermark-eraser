import os
base = r'C:\Users\Administrator\.openclaw\workspace\watermark-eraser\backend'

def w(rel, content):
    p = os.path.join(base, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)

w('requirements.txt', '''fastapi==0.115.0
uvicorn==0.30.0
sqlalchemy==2.0.35
pydantic==2.9.0
pydantic-settings==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
pillow==10.4.0
pyyaml==6.0.2
''')

w('.env.example', '''SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///./data.db
SMS_VERIFY_CODE=888888
''')

w('config.yaml', '''app:
  name: "水印去除工具"
  version: "1.0.0"
  debug: true
auth:
  secret_key: "dev-secret-key"
  token_expire_days: 7
upload:
  max_image_size: 31457280
  max_video_size: 524288000
  allowed_images: ["jpg", "jpeg", "png", "webp"]
  allowed_videos: ["mp4", "mov", "avi"]
  file_expire_hours: 24
points:
  register_bonus: 5
  sign_in_reward: 1
  sign_in_7_bonus: 3
  sign_in_30_bonus: 10
  invite_reward: 3
  cost:
    image_standard: 1
    image_hd: 3
    video_30s: 5
    video_3min: 15
    video_long: 30
watermark:
  active_engine: "placeholder"
''')

w('app/__init__.py', '')
w('app/models/__init__.py', 'from app.models.user import User\nfrom app.models.task import Task\nfrom app.models.order import VipOrder, PointOrder\nfrom app.models.point import PointLog, SignInLog\n')
w('app/schemas/__init__.py', '')
w('app/routers/__init__.py', '')
w('app/services/__init__.py', '')
w('app/services/watermark/__init__.py', '')
w('app/tasks/__init__.py', '')
w('app/utils/__init__.py', '')

print('part1 done')
