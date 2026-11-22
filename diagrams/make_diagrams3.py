# -*- coding: utf-8 -*-
"""Compact versions of all thesis diagrams: every label is at least 10 pt at the printed size.

Printed font size = font_px * printed_width_pt / canvas_width_px. Each figure is inserted with the
width returned by print_width_cm() so that the smallest label is 10.2 pt (never wider than 17.5 cm).

Run:  python make_diagrams3.py   -> *_v3.svg, then render to PNG with Chrome.
"""
import json
from make_diagrams import Svg, ellipse_edge, actor

F = 16           # base label size, px
MIN_PT = 10.2
specs = {}


def save(s, name, min_font):
    s.save(name + '.svg')
    w_pt = min(496.0, MIN_PT * s.w / min_font)
    specs[name] = {'w': s.w, 'h': s.h, 'min_font_px': min_font, 'width_cm': round(w_pt / 28.3465, 2),
                   'height_cm': round(w_pt / 28.3465 * s.h / s.w, 2), 'min_pt': round(min_font * w_pt / s.w, 1)}


def box(s, x, y, w, h, text, r=0, dash=False, size=F, bold=False):
    s.rect(x, y, w, h, r=r, dash=dash)
    n = text.count('\n')
    s.text(x + w / 2, y + h / 2 + size * 0.35 + (0 if n == 0 else 0), text, size, bold=bold)


def container(s, x, y, w, h, title, size=F):
    s.rect(x, y, w, h, fill='none', sw=1.2, dash=True)
    s.text(x + 12, y + 24, title, size, anchor='start', bold=True)


def group(s, x, y, w, title, items, cols, bh=46, gap=12, size=F):
    rows = (len(items) + cols - 1) // cols
    h = 40 + rows * (bh + gap) + 2
    s.rect(x, y, w, h, sw=1.2)
    s.text(x + 12, y + 26, title, size, anchor='start', bold=True)
    bw = (w - gap * (cols + 1)) / cols
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        box(s, x + gap + c * (bw + gap), y + 40 + r * (bh + gap), bw, bh, it, size=size)
    return y + h


# ---------------------------------------------------------------- 2.1 use cases
def use_case():
    FS = 17
    s = Svg(800, 900)
    s.rect(120, 20, 530, 870, sw=1.8)
    s.text(385, 48, 'Система Adaptive OST', FS + 1, bold=True)
    primary = ['Реєстрація', 'Вхід у систему', 'Ініціалізація моделі\nрозпізнавання', 'Налаштування інтервалу\nаналізу та гучності',
               'Запуск прослуховування\n(агентного циклу)', 'Перегляд результатів\nаналізу настрою', 'Ручний вибір настрою',
               'Зупинка прослуховування', 'Вихід із системи']
    RX, RY = 140, 34
    ax, ay = 52, 470
    pos = {}
    for i, name in enumerate(primary):
        cx, cy = 280, 100 + i * 92
        pos[name] = (cx, cy)
        s.line([(ax + 30, ay - 10), (cx - RX, cy)])
    for name, (cx, cy) in pos.items():
        s.ellipse(cx, cy, RX, RY)
        s.text(cx, cy + 6, name, FS)
    actor(s, ax, ay, '')
    s.text(ax, ay + 84, 'Корис-\nтувач\n(ведучий\nгри)', FS)
    inc = ['Захоплення\nаудіо', 'Розпізнавання\nмовлення', 'Аналіз настрою\nсцени', 'Автоматична\nзміна музики']
    start = pos[primary[4]]
    IRX = 100
    ipos = {}
    for i, name in enumerate(inc):
        cx, cy = 535, 250 + i * 120
        ipos[name] = (cx, cy)
        a = ellipse_edge(start[0], start[1], RX, RY, cx, cy)
        b = ellipse_edge(cx, cy, IRX, RY, start[0], start[1])
        s.line([a, b], arrow='open', dash=True)
    for i, (name, (cx, cy)) in enumerate(ipos.items()):
        s.ellipse(cx, cy, IRX, RY)
        s.text(cx, cy + 6 - FS * 0.6 + FS * 0.6, name, FS)
    s.text(470, 205, '«include»', FS, italic=True, bg=True)
    ex = (535, 790)
    s.ellipse(ex[0], ex[1], IRX + 10, RY + 6)
    s.text(ex[0], ex[1] + 6, 'Резервний аналіз\nза ключовими\nсловами', FS - 1 if False else FS)
    tgt = ipos['Аналіз настрою\nсцени']
    s.line([(ex[0], ex[1] - RY - 6), (tgt[0], tgt[1] + RY + 128)], arrow='open', dash=True)
    s.text(ex[0] + 8, ex[1] - 64, '«extend»', FS, anchor='start', italic=True, bg=True)
    actor(s, 745, 540, '')
    s.text(745, 625, 'Сервіс\nмовної\nмоделі', FS)
    s.line([(635, 610), (715, 545)])
    save(s, 'fig_2_1_use_case', FS)


# ---------------------------------------------------------------- 3.1 architecture
def architecture():
    s = Svg(760, 1000)
    W, H = 222, 76
    X = [24, 269, 514]
    container(s, 12, 12, 736, 420, 'Клієнтська частина: браузер (React 18, Vite)')
    box(s, X[1], 50, W, H, 'Інтерфейс\nкористувача\n(компоненти React)')
    box(s, X[0], 190, W, H, 'Захоплення аудіо\n(MediaRecorder)')
    box(s, X[1], 190, W, H, 'Сховище стану\n(Zustand)')
    box(s, X[2], 190, W, H, 'Аудіорушій\n(Web Audio API)')
    box(s, X[0], 330, W, H, 'Розпізнавання\nмовлення (Whisper,\nWebAssembly)')
    box(s, X[1], 330, W, H, 'Агентний цикл\n(useAgenticLoop,\nloopController)')
    box(s, X[2], 330, W, H, 'Клієнт API\n(moodAnalyzer,\nauthService)')
    cx = [x + W / 2 for x in X]
    s.line([(cx[1], 126), (cx[1], 190)], arrow='solid'); s.line([(cx[1], 190), (cx[1], 128)], arrow='solid')
    s.line([(cx[1], 266), (cx[1], 330)], arrow='solid'); s.line([(cx[1], 330), (cx[1], 268)], arrow='solid')
    s.line([(cx[0], 266), (cx[0], 330)], arrow='solid'); s.text(cx[0] + 8, 304, 'фрагмент', F, anchor='start')
    s.line([(X[0] + W, 368), (X[1], 368)], arrow='solid')
    s.line([(X[1] + W, 368), (X[2], 368)], arrow='solid')
    s.line([(X[1] + W - 30, 330), (X[2] + 30, 266)], arrow='solid'); s.text(X[2] + 40, 300, 'категорія', F, anchor='start')
    s.line([(cx[2], 406), (cx[2], 540)], arrow='solid'); s.line([(cx[2], 540), (cx[2], 408)], arrow='solid')
    s.text(cx[2] - 10, 470, 'REST / JSON (лише текст)', F, anchor='end', bg=True)
    container(s, 12, 500, 736, 340, 'Серверна частина: FastAPI (Python 3.10)')
    box(s, X[2], 540, W, H, 'Маршрутизатори\n(auth, mood,\ntranscribe, music)')
    box(s, X[1], 650, W, H, 'Автентифікація\n(JWT, bcrypt)')
    box(s, X[2], 650, W, H, 'Аналіз настрою\n(перевірка відповіді\nмоделі)')
    box(s, X[1], 744, W, 84, 'База даних SQLite\n(users,\nuser_preferences)', r=14)
    s.line([(cx[2], 616), (cx[2], 650)], arrow='solid')
    s.line([(X[2], 578), (cx[1], 578), (cx[1], 650)], arrow='solid')
    s.line([(cx[1], 726), (cx[1], 752)], arrow='solid'); s.line([(cx[1], 752), (cx[1], 728)], arrow='solid')
    container(s, 400, 880, 348, 108, 'Зовнішній сервіс')
    box(s, X[2], 912, W, 66, 'Groq API\n(мовна модель)')
    s.line([(cx[2], 726), (cx[2], 912)], arrow='solid'); s.line([(cx[2], 912), (cx[2], 728)], arrow='solid')
    s.text(cx[2] - 10, 860, 'HTTPS', F, anchor='end', bg=True)
    save(s, 'fig_3_1_architecture', F)


# ---------------------------------------------------------------- 3.2 modules
def modules():
    s = Svg(760, 980)
    s.rect(10, 10, 740, 640, fill='none', sw=1.2, dash=True)
    s.text(22, 34, 'Клієнтська частина: frontend/src/', F, anchor='start', bold=True)
    b1 = group(s, 26, 52, 708, 'components/', ['AuthPage.jsx', 'ControlPanel.jsx', 'MoodOrb.jsx', 'ListenerStatus.jsx',
                                                'EnvironmentDisplay.jsx', 'VolumeControl.jsx', 'TransitionLog.jsx', 'SettingsPanel.jsx'], 3)
    y2 = b1 + 36
    b2 = group(s, 26, y2, 460, 'hooks/', ['useAgenticLoop.js', 'useAudioCapture.js'], 2)
    group(s, 534, y2, 200, 'store/', ['useAppStore.js'], 1)
    y3 = b2 + 36
    b3 = group(s, 26, y3, 708, 'services/', ['loopController.js', 'whisperService.js', 'moodAnalyzer.js', 'audioEngine.js', 'musicService.js', 'authService.js'], 3)
    s.line([(250, b1), (250, y2)], arrow='solid')
    s.line([(634, b1), (634, y2)], arrow='solid')
    s.line([(486, y2 + 62), (534, y2 + 62)], arrow='solid')
    s.line([(250, b2), (250, y3)], arrow='solid')
    yb = b3 + 76
    s.line([(380, b3), (380, yb)], arrow='solid'); s.line([(380, yb), (380, b3 + 2)], arrow='solid')
    s.text(392, (b3 + yb) / 2 + 8, 'REST / JSON, префікс /api', F, anchor='start', bg=True)
    bend = group(s, 10, yb, 740, 'Серверна частина: backend/app/', ['main.py', 'config.py', 'database.py', 'auth.py',
                                                                  'routers/auth.py', 'routers/mood.py', 'routers/transcribe.py', 'routers/music.py'], 3)
    s.h = int(bend + 12)
    save(s, 'fig_3_2_modules', F)


# ---------------------------------------------------------------- sequence diagrams
def seq(name, names, msgs, loop_label, width=760, gap=None):
    n = len(names)
    gap = gap or (width - 160) / (n - 1)
    xs = [80 + i * gap for i in range(n)]
    step = 54
    lines_total = sum(1 + (m[2].count('\n') if isinstance(m, tuple) else 0) for m in msgs)
    h = 120 + len(msgs) * step + lines_total * 6 + 80
    s = Svg(width, h)
    top, bottom = 72, h - 64
    y = 120
    loop_y = None
    for m in msgs:
        if m == 'LOOP':
            loop_y = y - 10
            y += step
            continue
        if m == 'END':
            s.rect(14, loop_y, width - 28, y - loop_y - 18, dash=True, fill='none', sw=1.3)
            s.rect(14, loop_y, 62, 28, sw=1.3)
            s.text(45, loop_y + 20, 'loop', F, bold=True)
            s.text(84, loop_y + 20, loop_label, F, anchor='start', bg=True)
            y += 24
            continue
        a, b, label, dashed = m
        nl = label.count('\n')
        y += nl * 12
        if a == b:
            x = xs[a]
            if a == len(xs) - 1:
                s.line([(x, y - 14), (x - 40, y - 14), (x - 40, y + 10), (x - 2, y + 10)], arrow='solid')
                s.text(x - 48, y + 2 - nl * 10, label, F, anchor='end', bg=True)
            else:
                s.line([(x, y - 14), (x + 40, y - 14), (x + 40, y + 10), (x + 2, y + 10)], arrow='solid')
                s.text(x + 48, y + 2 - nl * 10, label, F, anchor='start', bg=True)
        else:
            x1, x2 = xs[a], xs[b]
            s.line([(x1, y), (x2 - 2 if x2 > x1 else x2 + 2, y)], arrow='open' if dashed else 'solid', dash=dashed)
            s.text((x1 + x2) / 2, y - 10 - nl * 19, label, F, bg=True)
        y += step
    bottom = y + 6
    s.h = int(bottom + 64)
    items, s.items = s.items, []
    for x in xs:                      # lifelines go under the message labels
        s.line([(x, top), (x, bottom)], sw=1.2)
    s.items += items
    for x, nm in zip(xs, names):
        for yy in (top - 54, bottom):
            s.rect(x - 70, yy, 140, 54, r=4)
            s.text(x, yy + 27 + 0.35 * F, nm, F)
    save(s, name, F)


def sequences():
    seq('fig_3_3_sequence_a', ['Ведучий\nгри', 'React UI', 'useAgentic\nLoop', 'Audio\nCapture', 'Whisper'], [
        (0, 1, 'Натискає\n«Start Listening»', False), (1, 3, 'startCapture()', False), (1, 2, 'loopController\n.start()', False),
        'LOOP',
        (2, 3, 'getAudioChunk()', False), (3, 2, 'Blob (WebM/Opus)', True), (2, 4, 'transcribeAudio(blob)', False), (4, 2, 'текст репліки', True),
        (2, 2, 'аналіз і зміна\nмузики (рис. 3.4)', False),
        'END',
        (0, 1, 'Натискає\n«Stop Listening»', False), (1, 3, 'stopCapture()', False), (1, 2, 'loopController\n.stop()', False),
    ], '[через 5 с, далі кожні N с]')
    seq('fig_3_3_sequence_b', ['useAgentic\nLoop', 'FastAPI', 'Groq API', 'AudioEngine'], [
        (0, 1, 'POST /api/analyze-\nmood {text}', False), (1, 2, 'chat.completions\n.create(prompt)', False),
        (2, 1, 'JSON {mood,\nintensity, ...}', True), (1, 1, 'validate_model\n_result()', False),
        (1, 0, '200 або 502', True), (0, 0, 'isStale()?\nshouldChange\nMusic()', False),
        (0, 3, 'crossfadeTo(mood, 3 с)', False), (3, 3, 'згасання 1,5 с,\nнаростання 1,5 с', False),
        (3, 0, 'перехід завершено', True),
    ], '', width=760)


# ---------------------------------------------------------------- 3.4 DFD
def dfd():
    s = Svg(780, 700)
    XL, XC, XR = 16, 290, 598
    WL, WC, WR = 180, 220, 166
    Y = [30, 160, 290, 420, 560]
    H = 84

    def ent(x, w, y, t):
        box(s, x, y, w, H, t, bold=True)

    def proc(y, t):
        box(s, XC, y, WC, H, t, r=24)

    ent(XL, WL, Y[0], 'Ведучий гри\n(мовлення)')
    proc(Y[0], '1. Захоплення\nаудіо')
    proc(Y[1], '2. Розпізнавання\nмовлення')
    proc(Y[2], '3. Аналіз настрою\n(сервер)')
    ent(XL, WL, Y[2], 'Сервіс мовної\nмоделі (Groq)')
    proc(Y[3], '4. Рішення про\nзміну музики')
    x, y = XL, Y[3]
    s.line([(x + WL, y), (x, y), (x, y + H), (x + WL, y + H)])
    s.line([(x + 30, y), (x + 30, y + H)], sw=1.2)
    s.text(x + 15, y + H / 2 + 6, 'D1', F)
    s.text(x + 30 + (WL - 30) / 2, y + H / 2 + 6, 'Стан,\nжурнал\nпереходів', F)
    ent(XR, WR, Y[3], 'Ведучий гри\n(інтерфейс)')
    proc(Y[4], '5. Синтез\nембієнту')
    ent(XR, WR, Y[4], 'Учасники\nгри (звук)')
    cx = XC + WC / 2

    def v(y1, y2, label):
        s.line([(cx, y1 + H), (cx, y2)], arrow='solid')
        s.text(cx + 10, (y1 + H + y2) / 2 + 6, label, F, anchor='start')

    def h(x1, x2, y, label, up=True):
        s.line([(x1, y), (x2, y)], arrow='solid')
        s.text((x1 + x2) / 2, y - 10 if up else y + 22, label, F, bg=True)

    h(XL + WL, XC, Y[0] + H / 2, 'аудіо')
    v(Y[0], Y[1], 'фрагмент WebM')
    v(Y[1], Y[2], 'текст репліки')
    h(XC, XL + WL, Y[2] + 28, 'промпт')
    h(XL + WL, XC, Y[2] + 60, 'JSON', up=False)
    v(Y[2], Y[3], 'настрій, середовище')
    h(XC, XL + WL, Y[3] + H / 2, 'запис')
    h(XC + WC, XR, Y[3] + H / 2, 'індикатори')
    v(Y[3], Y[4], 'категорія')
    h(XC + WC, XR, Y[4] + H / 2, 'звук')
    save(s, 'fig_3_4_dfd', F)


# ---------------------------------------------------------------- screens
def screens():
    FS = 17
    s = Svg(800, 790)
    s.add('<g transform="translate(0,30)">')
    W, H = 260, 78
    L, Rx = 96, 520
    box(s, L, 30, W, H, 'Сторінка входу\n«Welcome Back»', r=8, size=FS)
    box(s, Rx, 30, W, H, 'Сторінка реєстрації\n«Join the Quest»', r=8, size=FS)
    box(s, L, 210, W, H, 'Головна панель:\nмодель не\nзавантажено', r=8, size=FS)
    box(s, L, 390, W, H, 'Головна панель:\nготова (Idle)', r=8, size=FS)
    box(s, L, 570, W, H, 'Головна панель:\nпрослуховування\n(Active)', r=8, size=FS)
    box(s, Rx, 552, W, 114, 'Індикатор настрою:\nTRANQUIL,\nSUSPENSEFUL, EPIC,\nOMINOUS, MYSTERIOUS', r=8, size=FS)
    s.line([(L + W, 52), (Rx, 52)], arrow='solid'); s.text((L + W + Rx) / 2, 44 - 20, '«Create\nan account»', FS)
    s.line([(Rx, 88), (L + W, 88)], arrow='solid'); s.text((L + W + Rx) / 2, 112, '«Sign in»', FS)
    s.line([(L + W / 2, 108), (L + W / 2, 210)], arrow='solid'); s.text(L + W / 2 + 8, 164, 'успішний вхід', FS, anchor='start')
    s.line([(Rx + W / 2, 108), (Rx + W / 2, 249), (L + W, 249)], arrow='solid'); s.text(Rx + W / 2 + 8, 170, 'успішна\nреєстрація', FS, anchor='start')
    s.line([(L + W / 2, 288), (L + W / 2, 390)], arrow='solid'); s.text(L + W / 2 + 8, 344, '«Initialize Whisper AI»', FS, anchor='start')
    s.line([(L + 90, 468), (L + 90, 570)], arrow='solid'); s.text(L + 82, 524, '«Start\nListening»', FS, anchor='end')
    s.line([(L + 170, 570), (L + 170, 468)], arrow='solid'); s.text(L + 178, 524, '«Stop Listening»', FS, anchor='start')
    s.line([(L + W, 596), (Rx, 596)], arrow='solid'); s.text((L + W + Rx) / 2, 588, 'нова категорія', FS)
    s.line([(Rx, 640), (L + W, 640)], arrow='solid'); s.text((L + W + Rx) / 2, 664, 'наступна\nітерація', FS)
    for y in (249, 429, 609):
        s.line([(L, y), (50, y)])
    s.line([(50, 609), (50, 69), (L, 69)], arrow='solid')
    s.text(42, 160, '«Logout»', FS, anchor='middle', bg=True)
    s.add('</g>')
    save(s, 'fig_3_9_screens', FS)


# ---------------------------------------------------------------- 4.1 stack
def stack():
    s = Svg(760, 760)
    y = 12
    rows = [
        ('Інтерфейс користувача', ['React 18.3', 'Vite 5.4', 'Zustand 4.5', 'Tailwind CSS 3.4']),
        ('Обробка звуку та мовлення в браузері', ['Web Audio API', 'MediaRecorder', 'Transformers.js 3.8', 'Whisper tiny.en\n(WebAssembly)']),
        ('Серверна частина', ['Python 3.10', 'FastAPI 0.109', 'Pydantic 2.5', 'SQLite + aiosqlite']),
        ('Безпека', ['JWT (python-jose)', 'bcrypt (passlib)']),
        ('Зовнішні сервіси', ['Groq API', 'мовна модель (GROQ_MODEL)', 'клієнт openai 1.12\n(AsyncOpenAI)']),
    ]
    for title, items in rows:
        bh = 58 if any('\n' in i for i in items) else 46
        y = group(s, 10, y, 740, title, items, 2, bh=bh) + 14
    s.h = int(y)
    save(s, 'fig_4_1_stack', F)


# ---------------------------------------------------------------- 4.3 state
def state():
    s = Svg(720, 800)
    W, H = 200, 46
    cx = 220
    st = {'Idle': 80, 'Initializing': 180}
    chain = ['Recording', 'Processing', 'Transcribing', 'Analyzing', 'UpdatingMusic']
    for i, n in enumerate(chain):
        st[n] = 300 + i * 100
    s.add('<circle cx="%d" cy="26" r="9" fill="black"/>' % cx)
    s.line([(cx, 35), (cx, 70 - H / 2)], arrow='solid')
    container(s, 24, 240, 680, 540, 'Прослуховування')
    labels = [('Idle', 'Initializing', '«Initialize Whisper AI»'), ('Initializing', 'Recording', 'модель готова,\n«Start Listening»'),
              ('Recording', 'Processing', 'кінець інтервалу'), ('Processing', 'Transcribing', 'аудіо отримано'),
              ('Transcribing', 'Analyzing', 'текст розпізнано'), ('Analyzing', 'UpdatingMusic', 'відповідь отримано')]
    for a, b, lab in labels:
        s.line([(cx, st[a] + H / 2), (cx, st[b] - H / 2)], arrow='solid')
        s.text(cx + 10, (st[a] + st[b]) / 2 + 6 - lab.count('\n') * 9, lab, F, anchor='start')
    back = [('Processing', 'немає аудіоданих'), ('Transcribing', 'порожній текст\nабо артефакт'),
            ('Analyzing', 'відмова аналізу\nабо сесію зупинено'), ('UpdatingMusic', 'перехід завершено\nабо не потрібен')]
    bus = 670
    for n, lab in back:
        y = st[n]
        s.line([(cx + W / 2, y), (bus, y)])
        s.text(430, y - 8 - lab.count('\n') * 19, lab, F, anchor='start', bg=True)
    s.line([(bus, st['UpdatingMusic']), (bus, st['Recording']), (cx + W / 2, st['Recording'])], arrow='solid')
    # stop listening
    s.line([(24, 520), (8, 520), (8, st['Idle']), (cx - W / 2, st['Idle'])], arrow='solid')
    s.text(64, st['Idle'] - 40, '«Stop\nListening»', F)
    # error
    s.add('')
    ex, ey = 560, 170
    s.line([(cx + W / 2, st['Initializing']), (ex - 70, ey)], arrow='solid')
    s.text((cx + W / 2 + ex - 70) / 2, ey - 10, 'помилка', F)
    s.line([(ex, ey - H / 2), (ex, st['Idle']), (cx + W / 2, st['Idle'])], arrow='solid')
    s.text(ex + 8, 110, 'повторна\nспроба', F, anchor='start')
    for n, y in st.items():
        s.rect(cx - W / 2, y - H / 2, W, H, r=10)
        s.text(cx, y + 6, n, F)
    s.rect(ex - 70, ey - H / 2, 140, H, r=10)
    s.text(ex, ey + 6, 'Error', F)
    save(s, 'fig_4_3_state', F)


# ---------------------------------------------------------------- class diagrams
def cls(s, x, y, name, attrs, methods, w):
    lh = 24
    h1 = 38
    h2 = max(1, len(attrs)) * lh + 14
    h3 = max(1, len(methods)) * lh + 14
    s.rect(x, y, w, h1 + h2 + h3)
    s.text(x + w / 2, y + 26, name, F + 1, bold=True)
    s.line([(x, y + h1), (x + w, y + h1)], sw=1.2)
    s.line([(x, y + h1 + h2), (x + w, y + h1 + h2)], sw=1.2)
    for i, a in enumerate(attrs):
        s.text(x + 10, y + h1 + 24 + i * lh, a, F, anchor='start')
    for i, m in enumerate(methods):
        s.text(x + 10, y + h1 + h2 + 24 + i * lh, m, F, anchor='start')
    return (x + w / 2, y, y + h1 + h2 + h3, x, x + w)


def class_client():
    s = Svg(760, 760)
    a = cls(s, 220, 20, 'AgenticLoop', ['+isRunning: boolean', '+lastMood: string', '+lastIntensity: int'],
            ['+startLoop()', '+stopLoop()', '+runLoopIteration()'], 320)
    kids = [
        (20, 'LoopController', ['-sessionId: int', '-busy: boolean'], ['+start()', '+stop()', '+isRunning()', '+isBusy()']),
        (400, 'AudioCapture', ['-recorder: MediaRecorder', '-stream: MediaStream'], ['+startCapture()', '+stopCapture()', '+getAudioChunk()']),
    ]
    kids2 = [
        (20, 'WhisperService', ['-pipeline: Pipeline'], ['+initWhisper()', '+transcribeAudio()', '+isWhisperReady()']),
        (400, 'AudioEngine', ['-masterGain: GainNode', '+currentMood: string'], ['+crossfadeTo(): Promise', '+playImmediate()', '+setVolume()', '+stopAll()']),
    ]
    row1 = 300
    bottoms = []
    for x, n, at, me in kids:
        c = cls(s, x, row1, n, at, me, 340)
        bottoms.append(c)
    row2 = max(c[2] for c in bottoms) + 60
    for x, n, at, me in kids2:
        c = cls(s, x, row2, n, at, me, 340)
        bottoms.append(c)
    # dependencies
    for k, c in enumerate(bottoms):
        sx = a[3] + 40 + k * 80
        if c[1] == row1:
            s.line([(sx, a[2]), (sx, a[2] + 40), (c[0], a[2] + 40), (c[0], c[1])], arrow='open', dash=True)
        else:
            lane = 380
            s.line([(sx, a[2]), (sx, a[2] + 20 + k * 6), (lane - 10 + (k - 2) * 20, a[2] + 20 + k * 6), (lane - 10 + (k - 2) * 20, row2 - 30), (c[0], row2 - 30), (c[0], c[1])], arrow='open', dash=True)
    s.text(380, a[2] + 34, '«uses»', F, italic=True, bg=True)
    s.h = int(max(c[2] for c in bottoms) + 20)
    save(s, 'fig_4_2_class_client', F)


def class_data():
    s = Svg(760, 560)
    u = cls(s, 20, 20, 'User', ['+id: int', '+email: string', '+username: string', '+hashed_password: string',
                                '+created_at: datetime', '+is_active: boolean'], ['+register()', '+login()'], 330)
    p = cls(s, 20, u[2] + 70, 'UserPreferences', ['+user_id: int', '+default_mood: string', '+default_environment: string',
                                                   '+volume: float', '+analysis_interval: int'], [], 330)
    s.line([(u[0], u[2]), (p[0], p[1])])
    s.text(u[0] + 10, u[2] + 24, '1', F, anchor='start'); s.text(p[0] + 10, p[1] - 10, '1', F, anchor='start')
    s.text(u[0] - 10, (u[2] + p[1]) / 2 + 6, 'має', F, anchor='end', italic=True)
    a = cls(s, 410, 20, 'AgenticLoop', [], ['+runLoopIteration()'], 330)
    m = cls(s, 410, a[2] + 110, 'MoodRouter', [], ['+analyze_mood()', '+validate_model_result()', '+analyze_mood_mock()'], 330)
    s.line([(a[0], a[2]), (m[0], m[1])], arrow='open', dash=True)
    s.text(a[0] + 10, (a[2] + m[1]) / 2 + 6, '«calls API»', F, anchor='start', italic=True)
    s.h = int(max(p[2], m[2]) + 20)
    save(s, 'fig_4_2_class_data', F)


if __name__ == '__main__':
    use_case(); architecture(); modules(); sequences(); dfd(); screens(); stack(); state(); class_client(); class_data()
    json.dump(specs, open('specs_v3.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    for k, v in specs.items():
        print(k, v)
