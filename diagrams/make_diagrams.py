# -*- coding: utf-8 -*-
"""Generates the thesis diagrams as black-and-white SVG files (no external tools needed).

Run:  python make_diagrams.py        -> *.svg in this folder
Then: node render.mjs                -> *.png (uses the installed Chrome)
"""
import html

FONT = 'Arial, Helvetica, sans-serif'


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []

    def add(self, s):
        self.items.append(s)

    def text(self, x, y, s, size=16, anchor='middle', bold=False, italic=False, bg=False):
        lines = s.split('\n')
        y0 = y - (len(lines) - 1) * size * 0.6
        if bg:
            wmax = max(len(l) for l in lines) * size * 0.56 + 8
            hx = {'middle': x - wmax / 2, 'start': x - 4, 'end': x - wmax + 4}[anchor]
            self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="white"/>' % (hx, y0 - size, wmax, len(lines) * size * 1.2 + 1))
        for i, l in enumerate(lines):
            self.add('<text x="%.1f" y="%.1f" font-family="%s" font-size="%d" text-anchor="%s"%s%s>%s</text>' % (
                x, y0 + i * size * 1.2, FONT, size, anchor, ' font-weight="bold"' if bold else '',
                ' font-style="italic"' if italic else '', html.escape(l)))

    def rect(self, x, y, w, h, r=0, dash=False, fill='white', sw=1.6):
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d" fill="%s" stroke="black" stroke-width="%.1f"%s/>' % (
            x, y, w, h, r, fill, sw, ' stroke-dasharray="7 5"' if dash else ''))

    def ellipse(self, cx, cy, rx, ry):
        self.add('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="white" stroke="black" stroke-width="1.6"/>' % (cx, cy, rx, ry))

    def line(self, pts, arrow=None, dash=False, sw=1.6):
        """arrow: None | 'solid' (filled) | 'open'"""
        d = ' '.join('%.1f,%.1f' % p for p in pts)
        self.add('<polyline points="%s" fill="none" stroke="black" stroke-width="%.1f"%s%s/>' % (
            d, sw, ' stroke-dasharray="7 5"' if dash else '', ' marker-end="url(#%s)"' % arrow if arrow else ''))

    def render(self):
        defs = ('<defs>'
                '<marker id="solid" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 z" fill="black"/></marker>'
                '<marker id="open" markerWidth="13" markerHeight="12" refX="12" refY="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,6 L0,12" fill="none" stroke="black" stroke-width="1.6"/></marker>'
                '</defs>')
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="white"/>%s%s</svg>'
                % (self.w, self.h, self.w, self.h, defs, ''.join(self.items)))

    def save(self, name):
        open(name, 'w', encoding='utf-8').write(self.render())
        print('written', name)


def ellipse_edge(cx, cy, rx, ry, tx, ty):
    """Point on the ellipse border in the direction of (tx, ty)."""
    dx, dy = tx - cx, ty - cy
    k = ((dx / rx) ** 2 + (dy / ry) ** 2) ** 0.5
    return cx + dx / k, cy + dy / k


def actor(s, x, y, label):
    s.add('<circle cx="%d" cy="%d" r="16" fill="white" stroke="black" stroke-width="1.8"/>' % (x, y - 52))
    s.line([(x, y - 36), (x, y + 10)], sw=1.8)
    s.line([(x - 28, y - 18), (x + 28, y - 18)], sw=1.8)
    s.line([(x, y + 10), (x - 22, y + 44)], sw=1.8)
    s.line([(x, y + 10), (x + 22, y + 44)], sw=1.8)
    s.text(x, y + 70, label, 16)


# ====================================================================== 1. Use case diagram
def use_case():
    s = Svg(1420, 1180)
    s.rect(230, 30, 920, 1120, sw=1.8)
    s.text(690, 60, 'Система Adaptive OST', 18, bold=True)
    RX, RY = 185, 36
    primary = ['Реєстрація', 'Вхід у систему', 'Ініціалізація моделі\nрозпізнавання', 'Налаштування інтервалу\nаналізу та гучності',
               'Запуск прослуховування\n(агентного циклу)', 'Перегляд результатів\nаналізу настрою', 'Ручний вибір настрою',
               'Зупинка прослуховування', 'Вихід із системи']
    ax, ay = 100, 560
    pos = {}
    for i, name in enumerate(primary):
        cx, cy = 450, 125 + i * 115
        pos[name] = (cx, cy)
        s.line([(ax + 32, ay - 10), (cx - RX, cy)])
    for name, (cx, cy) in pos.items():
        s.ellipse(cx, cy, RX, RY)
        s.text(cx, cy + 6, name, 16)
    actor(s, ax, ay, 'Користувач\n(ведучий гри)')
    inc = ['Захоплення аудіо', 'Розпізнавання\nмовлення', 'Аналіз настрою сцени', 'Автоматична зміна\nмузики (кросфейд)']
    start = pos[primary[4]]
    ipos = {}
    for i, name in enumerate(inc):
        cx, cy = 930, 400 + i * 110
        ipos[name] = (cx, cy)
        a = ellipse_edge(start[0], start[1], RX, RY, cx, cy)
        b = ellipse_edge(cx, cy, 170, RY, start[0], start[1])
        s.line([a, b], arrow='open', dash=True)
        s.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 6, '«include»', 14, italic=True, bg=True)
    for name, (cx, cy) in ipos.items():
        s.ellipse(cx, cy, 170, RY)
        s.text(cx, cy + 6, name, 16)
    # extend
    ex_c = (930, 900)
    tgt = ipos['Аналіз настрою сцени']
    a = ellipse_edge(ex_c[0] + 120, ex_c[1], 60, RY, tgt[0] + 150, tgt[1])
    s.line([(1115, 900), (1132, 900), (1132, 665), (1075, 640)], arrow='open', dash=True)
    s.text(1124, 800, '«extend»', 14, anchor='end', italic=True, bg=True)
    s.ellipse(ex_c[0], ex_c[1], 185, RY)
    s.text(ex_c[0], ex_c[1] + 6, 'Резервний аналіз\nза ключовими словами', 16)
    # secondary actor
    actor(s, 1300, 620, 'Сервіс мовної\nмоделі (Groq API)')
    s.line([(1100, 620), (1268, 610)])
    s.save('fig_2_1_use_case.svg')


# ====================================================================== 2. State diagram
def state():
    s = Svg(1010, 960)
    W, H = 190, 46
    st = {'Idle': (430, 100), 'Initializing': (430, 220), 'Error': (130, 470), 'Recording': (430, 360), 'Processing': (430, 500),
          'Transcribing': (430, 630), 'Analyzing': (430, 760), 'UpdatingMusic': (430, 890)}
    s.add('<circle cx="430" cy="28" r="9" fill="black"/>')
    s.line([(430, 37), (430, 77)], arrow='solid')
    s.text(438, 62, 'Завантаження застосунку', 14, anchor='start')
    chain = [('Idle', 'Initializing', '«Initialize Whisper AI»,\n«Start Listening»'), ('Initializing', 'Recording', 'Модель готова,\nмікрофон доступний'),
             ('Recording', 'Processing', 'Таймер: через 5 с,\nдалі кожні 20 с'), ('Processing', 'Transcribing', 'Аудіо отримано'),
             ('Transcribing', 'Analyzing', 'Текст розпізнано'), ('Analyzing', 'UpdatingMusic', 'Вектор настрою отримано')]
    for a, b, label in chain:
        (x, y1), (_, y2) = st[a], st[b]
        s.line([(x, y1 + H / 2), (x, y2 - H / 2)], arrow='solid')
        s.text(x + 8, (y1 + y2) / 2 + 5, label, 14, anchor='start')
    back = [('Processing', 'Немає аудіоданих', 690, 348), ('Transcribing', 'Порожній текст або артефакт', 780, 356),
            ('Analyzing', 'Відмова аналізу або сесію зупинено', 850, 364), ('UpdatingMusic', 'Настрій не змінився або кросфейд запущено', 930, 372)]
    for name, label, cx, ry in back:
        x, y = st[name]
        s.line([(x + W / 2, y), (cx, y), (cx, ry), (430 + W / 2, ry)], arrow='solid')
        s.text(x + W / 2 + 10, y - 8, label, 14, anchor='start')
    # error handling
    s.line([(335, 220), (130, 220), (130, 470 - H / 2)], arrow='solid')
    s.text(138, 395, 'Помилка моделі\nабо мікрофона', 14, anchor='start')
    s.line([(35, 470), (15, 470), (15, 92), (335, 92)], arrow='solid')
    s.text(40, 84, 'Повторна спроба', 14, anchor='start')
    # stop
    s.line([(335, 360), (290, 360), (290, 112), (335, 112)], arrow='solid')
    s.text(284, 305, '«Stop Listening»', 14, anchor='end')
    for name, (x, y) in st.items():
        s.rect(x - W / 2, y - H / 2, W, H, r=10)
        s.text(x, y + 6, name, 16)
    s.save('fig_4_3_state.svg')


# ====================================================================== 3. Sequence diagram
def sequence():
    names = ['Ведучий гри', 'React UI', 'useAgenticLoop', 'AudioCapture', 'Whisper', 'FastAPI', 'Groq API', 'AudioEngine']
    xs = [90 + i * 180 for i in range(len(names))]
    msgs = [
        (0, 1, 'Натискає «Start Listening»', False), (1, 3, 'startCapture()', False), (1, 2, 'loopController.start()', False),
        (2, 7, 'playImmediate("calm")', False), (7, 0, 'Звучить ембієнт категорії calm', True), 'LOOP',
        (2, 3, 'getAudioChunk()', False), (3, 2, 'Blob (WebM/Opus)', True), (2, 4, 'transcribeAudio(blob)', False), (4, 2, 'текст репліки', True),
        (2, 5, 'POST /api/analyze-mood {text}', False), (5, 6, 'chat.completions.create(prompt)', False),
        (6, 5, 'JSON {mood, intensity, environment}', True), (5, 5, 'validate_model_result()', False), (5, 2, '200 MoodResponse або 502', True),
        (2, 2, 'isStale()? shouldChangeMusic()', False), (2, 7, 'crossfadeTo(mood, 3 с)', False), (7, 0, 'Зміна ембієнту', True), 'END',
        (0, 1, 'Натискає «Stop Listening»', False), (1, 3, 'stopCapture()', False), (1, 2, 'loopController.stop()', False),
    ]
    step = 46
    h = 110 + len(msgs) * step + 90
    s = Svg(xs[-1] + 110, h)
    top, bottom = 70, h - 70
    for x in xs:
        s.line([(x, top), (x, bottom)], sw=1.2)
    y = 110
    loop_y = None
    for m in msgs:
        if m == 'LOOP':
            loop_y = y - 8
            y += step
            continue
        if m == 'END':
            s.rect(xs[0] - 60, loop_y, xs[-1] - xs[0] + 130, y - loop_y - 14, dash=True, fill='none', sw=1.3)
            s.rect(xs[0] - 60, loop_y, 60, 26, sw=1.3)
            s.text(xs[0] - 30, loop_y + 18, 'loop', 14, bold=True)
            s.text(xs[0] + 20, loop_y + 18, '[через 5 с після старту, далі кожні 20 с]', 14, anchor='start', bg=True)
            y += 20
            continue
        a, b, label, dashed = m
        if a == b:
            x = xs[a]
            s.line([(x, y - 14), (x + 46, y - 14), (x + 46, y + 8), (x + 2, y + 8)], arrow='solid')
            s.text(x + 54, y + 2, label, 14, anchor='start', bg=True)
        else:
            x1, x2 = xs[a], xs[b]
            s.line([(x1, y), (x2 - 2 if x2 > x1 else x2 + 2, y)], arrow='open' if dashed else 'solid', dash=dashed)
            s.text((x1 + x2) / 2, y - 9, label, 14, bg=True)
        y += step
    for x, n in zip(xs, names):
        for yy in (top - 44, bottom):
            s.rect(x - 78, yy, 156, 44, r=4)
            s.text(x, yy + 28, n, 15)
    s.save('fig_3_3_sequence.svg')


# ====================================================================== 4. ER diagram
def table(s, x, y, name, rows, dash=False, w=430):
    rh = 36
    s.rect(x, y, w, rh * (len(rows) + 1), dash=dash)
    s.text(x + w / 2, y + 24, name, 16, bold=True)
    for i, (typ, col, key) in enumerate(rows):
        yy = y + rh * (i + 1)
        s.line([(x, yy), (x + w, yy)], sw=1.2, dash=dash)
        s.text(x + 12, yy + 24, typ, 15, anchor='start')
        s.text(x + 120, yy + 24, col, 15, anchor='start')
        s.text(x + w - 12, yy + 24, key, 15, anchor='end')
    s.line([(x + 108, y + rh), (x + 108, y + rh * (len(rows) + 1))], sw=1.2, dash=dash)
    return y + rh * (len(rows) + 1)


def table_big(s, x, y, name, rows, w=560, rh=44, fs=19):
    s.rect(x, y, w, rh * (len(rows) + 1))
    s.text(x + w / 2, y + rh * 0.68, name, fs + 1, bold=True)
    for i, (typ, col, key) in enumerate(rows):
        yy = y + rh * (i + 1)
        s.line([(x, yy), (x + w, yy)], sw=1.2)
        s.text(x + 12, yy + rh * 0.68, typ, fs, anchor='start')
        s.text(x + 150, yy + rh * 0.68, col, fs, anchor='start')
        s.text(x + w - 12, yy + rh * 0.68, key, fs, anchor='end')
    s.line([(x + 138, y + rh), (x + 138, y + rh * (len(rows) + 1))], sw=1.2)
    return y + rh * (len(rows) + 1)


def er():
    """Implemented schema only (users, user_preferences); fonts sized for >= 10 pt at 12.5 cm width."""
    s = Svg(640, 740)
    b1 = table_big(s, 40, 20, 'USERS', [('INTEGER', 'id', 'PK'), ('TEXT', 'email', 'UNIQUE, NOT NULL'), ('TEXT', 'username', 'NOT NULL'),
                                        ('TEXT', 'hashed_password', 'NOT NULL'), ('TIMESTAMP', 'created_at', ''), ('BOOLEAN', 'is_active', '')])
    y2 = b1 + 120
    b2 = table_big(s, 40, y2, 'USER_PREFERENCES', [('INTEGER', 'user_id', 'PK, FK'), ('TEXT', 'default_mood', ''),
                                                   ('TEXT', 'default_environment', ''), ('REAL', 'volume', ''), ('INTEGER', 'analysis_interval', '')])
    s.line([(320, b1), (320, y2)])
    s.text(334, b1 + 26, '1', 19, anchor='start')
    s.text(334, y2 - 10, '1', 19, anchor='start')
    s.text(306, b1 + 66, 'має', 19, anchor='end', italic=True)
    s.save('fig_3_5_er.svg')


def er_designed():
    s = Svg(1000, 1010)
    b1 = table(s, 285, 20, 'USERS', [('INTEGER', 'id', 'PK'), ('TEXT', 'email', 'UNIQUE, NOT NULL'), ('TEXT', 'username', 'NOT NULL'),
                                     ('TEXT', 'hashed_password', 'NOT NULL'), ('TIMESTAMP', 'created_at', ''), ('BOOLEAN', 'is_active', '')])
    y2 = b1 + 110
    b2 = table(s, 30, y2, 'USER_PREFERENCES', [('INTEGER', 'user_id', 'PK, FK'), ('TEXT', 'default_mood', ''), ('TEXT', 'default_environment', ''),
                                               ('REAL', 'volume', ''), ('INTEGER', 'analysis_interval', '')])
    b3 = table(s, 540, y2, 'SESSION_HISTORY', [('INTEGER', 'id', 'PK'), ('INTEGER', 'user_id', 'FK'), ('DATETIME', 'session_start', 'NOT NULL'),
                                              ('DATETIME', 'session_end', ''), ('INTEGER', 'total_mood_changes', '')], dash=True)
    y4 = b3 + 110
    b4 = table(s, 540, y4, 'MOOD_LOGS', [('INTEGER', 'id', 'PK'), ('INTEGER', 'session_id', 'FK'), ('TEXT', 'mood', 'NOT NULL'), ('INTEGER', 'intensity', 'NOT NULL'),
                                        ('TEXT', 'environment', 'NOT NULL'), ('TEXT', 'transcription', 'NOT NULL'), ('DATETIME', 'timestamp', '')], dash=True)
    s.line([(400, b1), (400, b1 + 55), (245, b1 + 55), (245, y2)])
    s.text(410, b1 + 22, '1', 15, anchor='start'); s.text(255, y2 - 10, '1', 15, anchor='start'); s.text(322, b1 + 48, 'має', 15, italic=True)
    s.line([(600, b1), (600, b1 + 55), (755, b1 + 55), (755, y2)], dash=True)
    s.text(610, b1 + 22, '1', 15, anchor='start'); s.text(765, y2 - 10, '0..*', 15, anchor='start'); s.text(678, b1 + 48, 'проводить', 15, italic=True)
    s.line([(755, b3), (755, y4)], dash=True)
    s.text(765, b3 + 22, '1', 15, anchor='start'); s.text(765, y4 - 10, '0..*', 15, anchor='start'); s.text(745, b3 + 60, 'містить', 15, anchor='end', italic=True)
    s.rect(30, b4 - 80, 60, 26); s.text(100, b4 - 61, 'таблицю створено в поточній збірці', 14, anchor='start')
    s.rect(30, b4 - 40, 60, 26, dash=True); s.text(100, b4 - 21, 'таблицю спроєктовано, не реалізовано', 14, anchor='start')
    s.save('fig_3_5_er_designed.svg')


# ====================================================================== 5. Class diagram
def cls(s, x, y, name, attrs, methods, w=250):
    lh = 22
    h1 = 36
    h2 = max(1, len(attrs)) * lh + 14
    h3 = max(1, len(methods)) * lh + 14
    s.rect(x, y, w, h1 + h2 + h3)
    s.text(x + w / 2, y + 24, name, 16, bold=True)
    s.line([(x, y + h1), (x + w, y + h1)], sw=1.2)
    s.line([(x, y + h1 + h2), (x + w, y + h1 + h2)], sw=1.2)
    for i, a in enumerate(attrs):
        s.text(x + 10, y + h1 + 22 + i * lh, a, 14, anchor='start')
    for i, m in enumerate(methods):
        s.text(x + 10, y + h1 + h2 + 22 + i * lh, m, 14, anchor='start')
    return (x + w / 2, y, y + h1 + h2 + h3)


def klass():
    s = Svg(1640, 760)
    u = cls(s, 30, 30, 'User', ['+id: int', '+email: string', '+username: string', '+hashed_password: string', '+created_at: datetime', '+is_active: boolean'],
            ['+register()', '+login()'])
    p = cls(s, 30, 420, 'UserPreferences', ['+user_id: int', '+default_mood: string', '+default_environment: string', '+volume: float', '+analysis_interval: int'], [])
    s.line([(u[0], u[2]), (p[0], p[1])])
    s.text(u[0] + 10, u[2] + 22, '1', 14, anchor='start'); s.text(p[0] + 10, p[1] - 10, '1', 14, anchor='start'); s.text(u[0] - 10, (u[2] + p[1]) / 2 + 5, 'має', 14, anchor='end', italic=True)
    a = cls(s, 830, 30, 'AgenticLoop', ['+isRunning: boolean', '+lastMood: string', '+lastIntensity: int'], ['+startLoop()', '+stopLoop()', '+runLoopIteration()'], w=270)
    kids = [
        ('LoopController', ['-sessionId: int', '-busy: boolean'], ['+start()', '+stop()', '+isRunning()', '+isBusy()'], 'uses'),
        ('AudioCapture', ['-recorder: MediaRecorder', '-stream: MediaStream'], ['+startCapture()', '+stopCapture()', '+getAudioChunk()'], 'uses'),
        ('WhisperService', ['-pipeline: Pipeline'], ['+initWhisper()', '+transcribeAudio()', '+isWhisperReady()'], 'uses'),
        ('AudioEngine', ['-audioContext: AudioContext', '-masterGain: GainNode', '+currentMood: string'], ['+init()', '+playImmediate()', '+crossfadeTo()', '+setVolume()', '+stopAll()'], 'uses'),
        ('MoodRouter', [], ['+analyze_mood()', '+validate_model_result()', '+analyze_mood_mock()'], 'calls API'),
    ]
    busy = 300
    for i, (name, attrs, methods, label) in enumerate(kids):
        x = 320 + i * 262
        c = cls(s, x, 420, name, attrs, methods, w=248)
        sx = a[0] - 100 + i * 50
        s.line([(sx, a[2]), (sx, busy + i * 0), (sx, 330), (c[0], 330), (c[0], c[1])], arrow='open', dash=True)
        s.text(c[0], 385, '«' + label + '»', 14, italic=True, bg=True)
    s.save('fig_4_2_class.svg')


if __name__ == '__main__':
    use_case(); state(); sequence(); er(); klass()
