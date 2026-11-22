# -*- coding: utf-8 -*-
"""Figures 3.1, 3.2, 3.4, 3.9 and 4.1 (black-and-white SVG). Uses helpers from make_diagrams.py."""
from make_diagrams import Svg


def box(s, x, y, w, h, text, r=0, dash=False, size=15, bold=False):
    s.rect(x, y, w, h, r=r, dash=dash)
    s.text(x + w / 2, y + h / 2 + 5, text, size, bold=bold)


def container(s, x, y, w, h, title):
    s.rect(x, y, w, h, fill='none', sw=1.2, dash=True)
    s.text(x + 14, y + 22, title, 15, anchor='start', bold=True)


def group(s, x, y, w, title, items, cols, bh=44, gap=14, size=15):
    """Titled container with a grid of boxes; returns bottom y."""
    rows = (len(items) + cols - 1) // cols
    h = 38 + rows * (bh + gap) + 4
    s.rect(x, y, w, h, sw=1.2)
    s.text(x + 14, y + 24, title, 15, anchor='start', bold=True)
    bw = (w - gap * (cols + 1)) / cols
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        box(s, x + gap + c * (bw + gap), y + 38 + r * (bh + gap), bw, bh, it, size=size)
    return y + h


# ====================================================================== Fig. 3.1 architecture
def architecture():
    s = Svg(1000, 1010)
    W, H = 240, 64
    container(s, 30, 20, 940, 380, 'Клієнтська частина: браузер (React 18, Vite)')
    box(s, 380, 60, W, H, 'Інтерфейс користувача\n(компоненти React)')
    box(s, 60, 180, W, H, 'Захоплення аудіо\n(MediaRecorder)')
    box(s, 380, 180, W, H, 'Сховище стану\n(Zustand)')
    box(s, 700, 180, W, H, 'Аудіорушій\n(Web Audio API)')
    box(s, 60, 300, W, H, 'Розпізнавання мовлення\n(Whisper, WebAssembly)')
    box(s, 380, 300, W, H, 'Агентний цикл\n(useAgenticLoop, loopController)', size=14)
    box(s, 700, 300, W, H, 'Клієнт API\n(moodAnalyzer, authService)')
    s.line([(500, 124), (500, 180)], arrow='solid'); s.line([(500, 180), (500, 126)], arrow='solid')
    s.line([(500, 244), (500, 300)], arrow='solid'); s.line([(500, 300), (500, 246)], arrow='solid')
    s.line([(180, 244), (180, 300)], arrow='solid'); s.text(188, 277, 'аудіофрагмент', 13, anchor='start')
    s.line([(300, 332), (380, 332)], arrow='solid'); s.text(340, 324, 'текст', 13)
    s.line([(620, 332), (700, 332)], arrow='solid'); s.text(660, 324, 'текст', 13)
    s.line([(600, 300), (720, 244)], arrow='solid'); s.text(690, 280, 'категорія', 13, anchor='start')
    s.line([(820, 364), (820, 520)], arrow='solid'); s.line([(820, 520), (820, 366)], arrow='solid')
    s.text(830, 440, 'REST / JSON (лише текст транскрипції)', 14, anchor='end', bg=True)
    container(s, 30, 470, 940, 370, 'Серверна частина: FastAPI (Python 3.10)')
    box(s, 700, 520, W, H, 'Маршрутизатори FastAPI\n(auth, mood, transcribe, music)', size=14)
    box(s, 380, 640, W, H, 'Автентифікація\n(JWT, bcrypt)')
    box(s, 700, 640, W, H, 'Аналіз настрою\n(валідація відповіді моделі)', size=14)
    box(s, 380, 750, W, H, 'База даних SQLite\n(users, user_preferences)', r=14, size=14)
    s.line([(820, 584), (820, 640)], arrow='solid')
    s.line([(700, 552), (500, 552), (500, 640)], arrow='solid')
    s.line([(500, 704), (500, 750)], arrow='solid'); s.line([(500, 750), (500, 706)], arrow='solid')
    container(s, 560, 890, 410, 105, 'Зовнішній сервіс')
    box(s, 700, 920, W, 60, 'Groq API\n(мовна модель, GROQ_MODEL)', size=14)
    s.line([(820, 704), (820, 920)], arrow='solid'); s.line([(820, 920), (820, 706)], arrow='solid')
    s.text(830, 868, 'HTTPS', 14, anchor='start', bg=True)
    s.save('fig_3_1_architecture.svg')


# ====================================================================== Fig. 3.2 modules
def modules():
    s = Svg(1120, 860)
    s.rect(20, 20, 1080, 590, fill='none', sw=1.2, dash=True)
    s.text(34, 42, 'Клієнтська частина: frontend/src/', 15, anchor='start', bold=True)
    b1 = group(s, 50, 60, 1020, 'components/', ['AuthPage.jsx', 'ControlPanel.jsx', 'MoodOrb.jsx', 'ListenerStatus.jsx',
                                                 'EnvironmentDisplay.jsx', 'VolumeControl.jsx', 'TransitionLog.jsx', 'SettingsPanel.jsx'], 4)
    y2 = b1 + 40
    b2 = group(s, 50, y2, 600, 'hooks/', ['useAgenticLoop.js', 'useAudioCapture.js'], 2)
    group(s, 730, y2, 340, 'store/', ['useAppStore.js'], 1)
    y3 = b2 + 40
    b3 = group(s, 50, y3, 1020, 'services/', ['loopController.js', 'whisperService.js', 'moodAnalyzer.js', 'audioEngine.js', 'musicService.js', 'authService.js'], 3)
    s.line([(350, b1), (350, y2)], arrow='solid')
    s.line([(900, b1), (900, y2)], arrow='solid')
    s.line([(650, y2 + 50), (730, y2 + 50)], arrow='solid')
    s.line([(350, b2), (350, y3)], arrow='solid')
    yb = 690
    s.line([(560, b3), (560, yb)], arrow='solid'); s.line([(560, yb), (560, b3 + 2)], arrow='solid')
    s.text(572, (b3 + yb) / 2 + 12, 'REST / JSON, префікс /api', 14, anchor='start', bg=True)
    group(s, 20, yb, 1080, 'Серверна частина: backend/app/', ['main.py', 'config.py', 'database.py', 'auth.py',
                                                              'routers/auth.py', 'routers/mood.py', 'routers/transcribe.py', 'routers/music.py'], 4)
    s.save('fig_3_2_modules.svg')


# ====================================================================== Fig. 3.4 DFD
def dfd():
    s = Svg(1120, 720)
    X = [50, 430, 810]
    Y = [40, 220, 400, 580]
    W, H = 260, 76

    def ent(c, r, t):
        box(s, X[c], Y[r], W, H, t, bold=True)

    def proc(c, r, t):
        box(s, X[c], Y[r], W, H, t, r=26)

    def store(c, r, t):
        x, y = X[c], Y[r]
        s.line([(x + W, y), (x, y), (x, y + H), (x + W, y + H)])
        s.line([(x + 26, y), (x + 26, y + H)], sw=1.2)
        s.text(x + 13, y + H / 2 + 5, 'D1', 14)
        s.text(x + 26 + (W - 26) / 2, y + H / 2 + 5, t, 15)

    ent(0, 0, 'Ведучий гри\n(мовлення)')
    proc(1, 0, '1. Захоплення аудіо\n(MediaRecorder)')
    proc(2, 0, '2. Розпізнавання мовлення\n(Whisper у браузері)')
    ent(0, 1, 'Сервіс мовної моделі\n(Groq API)')
    proc(1, 1, '3. Аналіз настрою\n(сервер FastAPI)')
    store(0, 2, 'Стан застосунку,\nжурнал переходів')
    proc(1, 2, '4. Рішення про зміну музики,\nоновлення стану')
    proc(2, 2, '5. Синтез ембієнту\nта кросфейд')
    ent(0, 3, 'Ведучий гри\n(інтерфейс)')
    ent(2, 3, 'Учасники гри\n(звук)')

    def harrow(c1, c2, r, label, dy=0):
        if c1 < c2:
            a, b = X[c1] + W, X[c2]
        else:
            a, b = X[c1], X[c2] + W
        y = Y[r] + H / 2 + dy
        s.line([(a, y), (b, y)], arrow='solid')
        s.text((a + b) / 2, y - 9, label, 13, bg=True)

    def varrow(c, r1, r2, label):
        x = X[c] + W / 2
        s.line([(x, Y[r1] + H), (x, Y[r2])], arrow='solid')
        s.text(x + 8, (Y[r1] + H + Y[r2]) / 2 + 5, label, 13, anchor='start')

    harrow(0, 1, 0, 'аудіосигнал')
    harrow(1, 2, 0, 'фрагмент WebM')
    x = X[2] + W / 2
    s.line([(x, Y[0] + H), (x, Y[1] + H / 2), (X[1] + W, Y[1] + H / 2)], arrow='solid')
    s.text(x + 8, Y[0] + H + 40, 'текст репліки', 13, anchor='start')
    harrow(1, 0, 1, 'текст і промпт', dy=-16)
    harrow(0, 1, 1, 'JSON-відповідь', dy=18)
    varrow(1, 1, 2, 'вектор настрою (mood, intensity, environment)')
    harrow(1, 0, 2, 'настрій, запис')
    harrow(1, 2, 2, 'категорія')
    varrow(0, 2, 3, 'індикатори, журнал')
    varrow(2, 2, 3, 'аудіопотік')
    s.save('fig_3_4_dfd.svg')


# ====================================================================== Fig. 3.9 screen transitions
def screens():
    s = Svg(1060, 760)
    W, H = 300, 70
    box(s, 300, 40, W, H, 'Сторінка входу\n«Welcome Back»', r=8)
    box(s, 720, 40, W, H, 'Сторінка реєстрації\n«Join the Quest»', r=8)
    box(s, 300, 220, W, H, 'Головна панель:\nмодель не завантажено', r=8)
    box(s, 300, 400, W, H, 'Головна панель:\nготова до роботи (Idle)', r=8)
    box(s, 300, 580, W, H, 'Головна панель:\nпрослуховування (Active)', r=8)
    box(s, 720, 565, W, 100, 'Індикатор настрою:\nTRANQUIL, SUSPENSEFUL, EPIC,\nOMINOUS, MYSTERIOUS', r=8, size=14)
    s.line([(600, 60), (720, 60)], arrow='solid'); s.text(660, 51, '«Create an account»', 13)
    s.line([(720, 92), (600, 92)], arrow='solid'); s.text(660, 110, '«Sign in»', 13)
    s.line([(450, 110), (450, 220)], arrow='solid'); s.text(458, 170, 'успішний вхід', 13, anchor='start')
    s.line([(870, 110), (870, 255), (600, 255)], arrow='solid'); s.text(878, 190, 'успішна\nреєстрація', 13, anchor='start')
    s.line([(450, 290), (450, 400)], arrow='solid'); s.text(458, 350, '«Initialize Whisper AI»', 13, anchor='start')
    s.line([(420, 470), (420, 580)], arrow='solid'); s.text(412, 530, '«Start Listening»', 13, anchor='end')
    s.line([(480, 580), (480, 470)], arrow='solid'); s.text(488, 530, '«Stop Listening»', 13, anchor='start')
    s.line([(600, 600), (720, 600)], arrow='solid'); s.text(660, 591, 'нова категорія', 13)
    s.line([(720, 632), (600, 632)], arrow='solid'); s.text(660, 650, 'наступна ітерація', 13)
    for y in (255, 435, 615):
        s.line([(300, y), (150, y)])
    s.line([(150, 615), (150, 75), (300, 75)], arrow='solid')
    s.text(142, 340, '«Logout»', 13, anchor='end')
    s.save('fig_3_9_screens.svg')


# ====================================================================== Fig. 4.1 technology stack
def stack():
    s = Svg(1120, 640)
    y = 20
    rows = [
        ('Інтерфейс користувача', ['React 18.3', 'Vite 5.4', 'Zustand 4.5', 'Tailwind CSS 3.4']),
        ('Обробка звуку та мовлення в браузері', ['Web Audio API', 'MediaRecorder', 'Transformers.js 3.8', 'Whisper tiny.en (WebAssembly)']),
        ('Серверна частина', ['Python 3.10', 'FastAPI 0.109', 'Pydantic 2.5', 'SQLite + aiosqlite']),
        ('Безпека', ['JWT (python-jose)', 'bcrypt (passlib)']),
        ('Зовнішні сервіси', ['Groq API', 'мовна модель (GROQ_MODEL)', 'клієнт openai 1.12 (AsyncOpenAI)']),
    ]
    for title, items in rows:
        y = group(s, 20, y, 1080, title, items, 4, size=14) + 18
    s.save('fig_4_1_stack.svg')


if __name__ == '__main__':
    architecture(); modules(); dfd(); screens(); stack()
