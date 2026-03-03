import sys
import random
import math
import json
import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect, QRectF, QPointF, QSize, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent

def resource_path(relative_path):
    """ PyInstaller용 리소스 경로 탐색 함수 """
    try:
        # PyInstaller가 임시 폴더에 리소스를 풀었을 때의 경로 (_MEIPASS)
        base_path = sys._MEIPASS
    except Exception:
        # 일반 개발 환경에서의 경로
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- 물고기 클래스 ---
class Fish:
    def __init__(self, name, x, y):
        self.name, self.x, self.y = name, float(x), float(y)
        self.target_x, self.target_y = random.randint(50, 350), random.randint(50, 250)
        self.speed, self.direction = random.uniform(0.3, 0.6), 1
        self.angle_offset = random.uniform(0, 10)
        self.is_dancing = False
        self.dance_timer = 0
        self.total_dance_time = 90
        self.scale = 1.0
        self.rotation = 0
        self.is_temp = False

    def start_dance(self):
        self.is_dancing = True
        self.dance_timer = self.total_dance_time
        self.scale = 3.0
        self.rotation = 0

    def move(self):
        if self.is_dancing:
            self.dance_timer -= 1
            self.rotation += 12
            if self.dance_timer <= 0:
                self.is_dancing, self.scale, self.rotation = False, 1.0, 0
            return
        dx, dy = self.target_x - self.x, self.target_y - self.y
        dist = math.sqrt(dx ** 2 + dy ** 2)
        if dist > 1.0:
            angle = math.atan2(dy, dx)
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
            self.direction = 1 if dx > 0.1 else -1
        else:
            self.target_x, self.target_y = random.randint(20, 380), random.randint(50, 280)

    def get_animated_pos(self, tick):
        if self.is_dancing: return self.x, self.y
        return self.x, self.y + math.sin(tick * 0.05 + self.angle_offset) * 2

# --- 장식 및 기포 클래스 ---
class Decoration:
    def __init__(self, name, x, y):
        self.name, self.x, self.y = name, x, y

class Bubble:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed, self.size = random.uniform(0.8, 1.8), random.randint(5, 10)
    def rise(self): self.y -= self.speed

# --- 메인 앱 클래스 ---
class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 400, 300)

        self.inherently_right_facing = ["goldfish", "angelfish", "gupy", "neontetra", "turtle"]
        self.available_fish_list = ["goldfish", "angelfish", "shrimp", "neontetra", "turtle", "gupy", "jellyfish", "blue_beta", "pink_beta", "yellow_beta", "clownfish", "whale", "seahorse", "chaeyeong"]
        self.fish_names_kor = {"goldfish": "금붕어", "angelfish": "엔젤피쉬", "shrimp": "새우", "neontetra": "네온테트라", "turtle": "거북이", "gupy": "구피", "jellyfish": "해파리", "blue_beta": "파란색 베타", "pink_beta": "분홍색 베타", "yellow_beta": "노란색 베타", "clownfish": "흰동가리", "whale": "고래", "seahorse": "해마", "chaeyeong": "챙이"}
        self.available_deco_list = ["pink_sanho", "blue_sanho", "blue_sanho2", "red_sanho", "red_sanho2", "purple_sanho", "orange_sanho", "dasima", "haecho1", "haecho2", "white_sand", "white_sand2", "gold_sand", "pink_sand", "rocks", "big_rocks", "rocks1", "starfish", "cool_crab", "seashell", "pink_conch", "blue_conch", "paper", "glass_bottle", "treasure_box", "dance"]
        self.deco_names_kor = {"pink_sanho": "분홍 산호초", "blue_sanho": "푸른 산호초", "blue_sanho2": "푸른 산호초", "red_sanho": "붉은 산호초", "red_sanho2": "붉은 산호초2", "purple_sanho": "보라색 산호초", "orange_sanho": "주황색 산호초", "dasima": "다시마", "haecho1": "해초1", "haecho2": "해초2", "white_sand": "흰모래 바닥1", "white_sand2": "흰모래 바닥2", "gold_sand": "금빛 모래 바닥", "pink_sand": "분홍빛 모래 바닥", "rocks": "돌더미 바닥", "big_rocks": "커다란 돌", "rocks1": "넓적 돌", "starfish": "불가사리", "cool_crab": "멋쟁이 게", "seashell": "조개", "pink_conch": "분홍 소라", "blue_conch": "파란 소라", "paper": "편지",  "glass_bottle": "유리병", "treasure_box": "보물상자", "dance": "???"}

        # 바닥 고정 에셋 리스트 정의
        self.floor_assets = ["white_sand", "white_sand2", "gold_sand", "pink_sand", "rocks"]

        self.fish_images, self.deco_images = {}, {}
        self.fishes, self.active_decorations, self.bubbles = [], [], []
        self.bubble_level, self.edit_mode, self.selected_deco = 5, False, None
        self.global_tick, self.offset = 0, None

        self.init_sound()
        self.load_resources()
        self.load_data()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_aquarium)
        self.timer.start(30)
        self.initUI()

    def init_sound(self):
        self.playlist = QMediaPlaylist()
        url = QUrl.fromLocalFile(resource_path("sound/underwater.mp3"))
        self.playlist.addMedia(QMediaContent(url))
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.player = QMediaPlayer()
        self.player.setPlaylist(self.playlist)
        self.player.setVolume(50)

    def load_resources(self):
        for n in self.available_fish_list:
            path = resource_path(f"fish_list/{n}.png")  # 👈 수정
            p = QPixmap(path)
            if not p.isNull():
                self.fish_images[n] = p.scaled(30, 30, Qt.KeepAspectRatio, Qt.FastTransformation)
        for n in self.available_deco_list:
            path = resource_path(f"deco_list/{n}.png")  # 👈 수정
            p = QPixmap(path)
            if not p.isNull():
                self.deco_images[n] = p

    def save_data(self):
        data = {
            "fishes": [{"name": f.name, "x": f.x, "y": f.y} for f in self.fishes if not f.is_temp],
            "decorations": [{"name": d.name, "x": d.x, "y": d.y} for d in self.active_decorations],
            "bubble_level": self.bubble_level,
            "sound_on": self.player.state() == QMediaPlayer.PlayingState
        }
        with open("save_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self):
        try:
            with open("save_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.bubble_level = data.get("bubble_level", 5)
                if data.get("sound_on", False): self.player.play()
                for fi in data.get("fishes", []): self.fishes.append(Fish(fi["name"], fi["x"], fi["y"]))
                for di in data.get("decorations", []):
                    # 불러올 때도 바닥 에셋이면 좌표 강제 교정 (옵션)
                    self.active_decorations.append(Decoration(di["name"], di["x"], di["y"]))
        except FileNotFoundError: pass

    def closeEvent(self, event):
        self.save_data(); event.accept()

    def initUI(self):
        layout = QVBoxLayout(); top_bar = QHBoxLayout()
        btns = [
            (resource_path('button/settings_btn.png'), self.dialog_open),
            (resource_path('button/hide_btn.png'), self.showMinimized),
            (resource_path('button/quit_btn.png'), self.close)
        ]
        for img, slot in btns:
            btn = QPushButton(); btn.setIcon(QIcon(img)); btn.setIconSize(QSize(25, 25))
            btn.setFixedSize(25, 25); btn.setStyleSheet("background: transparent; border: none;")
            btn.clicked.connect(slot); top_bar.addWidget(btn)
        top_bar.insertStretch(0); layout.addLayout(top_bar); layout.addStretch(); self.setLayout(layout)

    def update_aquarium(self):
        self.global_tick += 1
        for f in self.fishes[:]:
            f.move()
            if f.is_temp and not f.is_dancing: self.fishes.remove(f)
        if self.bubble_level > 0 and random.random() < self.bubble_level * 0.015:
            self.bubbles.append(Bubble(random.randint(10, self.width() - 10), self.height()))
        for b in self.bubbles[:]:
            b.rise()
            if b.y < -20: self.bubbles.remove(b)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self);
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. 배경 그라데이션 (가장 뒤)
        for y in range(0, self.height(), 50):
            r = y / self.height()
            painter.setBrush(
                QColor(int(100 * (1 - r) + 20 * r), int(200 * (1 - r) + 50 * r), int(255 * (1 - r) + 100 * r), 180))
            painter.setPen(Qt.NoPen);
            painter.drawRect(0, y, self.width(), 50)

        # 2. 기포 그리기
        painter.setPen(QPen(Qt.white, 1))
        painter.setBrush(Qt.NoBrush)
        for b in self.bubbles: painter.drawEllipse(int(b.x), int(b.y), b.size, b.size)

        # 3. 장식 그리기 (레이어 분리)
        # 단계 A: 바닥 에셋들을 먼저 그립니다 (제일 뒤로 배치)
        for d in self.active_decorations:
            if d.name in self.floor_assets and d.name in self.deco_images:  #
                img = self.deco_images[d.name]
                painter.drawPixmap(int(d.x), int(d.y), img)

        # 단계 B: 일반 장식들을 그 위에 그립니다
        for d in self.active_decorations:
            if d.name not in self.floor_assets and d.name in self.deco_images:  #
                img = self.deco_images[d.name]
                painter.drawPixmap(int(d.x), int(d.y), img)

        # 4. 물고기 그리기 (가장 앞)
        for f in self.fishes:
            cur_x, cur_y = f.get_animated_pos(self.global_tick)
            if f.name in self.fish_images:
                img = self.fish_images[f.name]
                if f.scale != 1.0: img = img.scaled(int(30 * f.scale), int(30 * f.scale), Qt.KeepAspectRatio,
                                                    Qt.FastTransformation)
                nat_dir = 1 if f.name in self.inherently_right_facing else -1
                if f.direction != nat_dir: img = img.transformed(QTransform().scale(-1, 1))
                painter.save();
                painter.translate(cur_x, cur_y);
                painter.rotate(f.rotation)
                painter.drawPixmap(int(-img.width() / 2), int(-img.height() / 2), img);
                painter.restore()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self.edit_mode:
                for d in reversed(self.active_decorations):
                    # 바닥 에셋은 드래그 대상에서 제외
                    if d.name in self.floor_assets: continue
                    img = self.deco_images.get(d.name)
                    if img and QRect(int(d.x), int(d.y), img.width(), img.height()).contains(e.pos()):
                        self.selected_deco, self.drag_offset = d, e.pos() - QPoint(int(d.x), int(d.y)); return
            # 편집 모드일 때는 창 이동용 offset을 잡지 않음
            if not self.edit_mode:
                self.offset = e.pos()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            if self.selected_deco:
                pos = e.pos() - self.drag_offset
                self.selected_deco.x, self.selected_deco.y = pos.x(), pos.y()
            # 👉 편집 모드가 아닐 때만 창 이동
            elif self.offset and not self.edit_mode:
                self.move(self.pos() + e.pos() - self.offset)

    def mouseReleaseEvent(self, e):
        self.offset, self.selected_deco = None, None

    def dialog_open(self):
        self.dialog = QDialog(self); self.dialog.setWindowTitle('설정'); self.dialog.setFixedSize(500, 700)
        main_layout = QVBoxLayout(self.dialog); lists_layout = QHBoxLayout()
        for title, items, names, active, toggle in [
            ("물고기 목록", self.available_fish_list, self.fish_names_kor, self.fishes, self.toggle_fish),
            ("장식 목록", self.available_deco_list, self.deco_names_kor, self.active_decorations, self.toggle_deco)
        ]:
            group = QGroupBox(title); vbox = QVBoxLayout(); scroll = QScrollArea(); widget = QWidget(); inner = QVBoxLayout(widget)
            for n in items:
                cb = QCheckBox(names.get(n, n)); cb.setChecked(any(x.name == n for x in active))
                cb.stateChanged.connect(lambda s, name=n, func=toggle: func(s, name)); inner.addWidget(cb)
            scroll.setWidget(widget); scroll.setWidgetResizable(True); vbox.addWidget(scroll); group.setLayout(vbox); lists_layout.addWidget(group)
        main_layout.addLayout(lists_layout)
        grid = QGridLayout()
        grid.addWidget(QLabel("🫧 기포 생성 주기:"), 0, 0)
        slider = QSlider(Qt.Horizontal); slider.setRange(0, 10); slider.setValue(self.bubble_level)
        slider.valueChanged.connect(self.set_bubble_rate); grid.addWidget(slider, 0, 1)
        self.sound_cb = QCheckBox("🔊 수중 소리 켜기"); self.sound_cb.setChecked(self.player.state() == QMediaPlayer.PlayingState)
        self.sound_cb.stateChanged.connect(self.toggle_sound); grid.addWidget(self.sound_cb, 1, 0, 1, 2)
        self.btn_edit_deco = QPushButton(); self.btn_edit_deco.setCheckable(True); self.btn_edit_deco.setChecked(self.edit_mode)
        self.btn_edit_deco.clicked.connect(self.toggle_edit_mode); self.update_edit_button_style()
        grid.addWidget(self.btn_edit_deco, 2, 0, 1, 2); main_layout.addLayout(grid); self.dialog.show()

    def toggle_sound(self, state):
        if state == Qt.Checked: self.player.play()
        else: self.player.stop()

    def toggle_edit_mode(self):
        self.edit_mode = self.btn_edit_deco.isChecked(); self.update_edit_button_style(); self.update()

    def update_edit_button_style(self):
        style = "padding: 10px; background-color: #4CAF50; color: white; font-weight: bold; border-radius: 5px;" if self.edit_mode else "padding: 10px; background-color: #f0f0f0; color: black; border: 1px solid #ccc; border-radius: 5px;"
        self.btn_edit_deco.setText("✅ 장식 편집 모드 ON" if self.edit_mode else "🖼️ 장식 편집 모드"); self.btn_edit_deco.setStyleSheet(style)

    def toggle_fish(self, s, n):
        if s == Qt.Checked: self.fishes.append(Fish(n, random.randint(50, 350), random.randint(50, 250)))
        else: self.fishes = [x for x in self.fishes if x.name != n]

    def toggle_deco(self, s, n):
        if s == Qt.Checked:
            if n == "dance": self.trigger_chaeyeong_dance()
            elif n in self.floor_assets:
                # 👉 바닥 에셋 하단 밀착 로직
                img = self.deco_images.get(n)
                img_h = img.height() if img else 50
                fixed_y = self.height() - img_h
                self.active_decorations.append(Decoration(n, 0, fixed_y))
            else: self.active_decorations.append(Decoration(n, random.randint(50, 300), random.randint(230, 260)))
        else:
            if n != "dance": self.active_decorations = [x for x in self.active_decorations if x.name != n]

    def trigger_chaeyeong_dance(self):
        target = next((f for f in self.fishes if f.name == "chaeyeong"), None)
        if target: target.start_dance()
        else:
            temp = Fish("chaeyeong", 200, 150); temp.is_temp = True; temp.start_dance(); self.fishes.append(temp)

    def set_bubble_rate(self, v): self.bubble_level = v

if __name__ == '__main__':
    app = QApplication(sys.argv); ex = MyApp(); ex.show(); sys.exit(app.exec_())