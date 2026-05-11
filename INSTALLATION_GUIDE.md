# VIGIL Stones — Kurulum ve Entegrasyon Rehberi

> Bu rehber, VIGIL Stones ve THE ARC sistemlerini kendi AI asistan projenize entegre etmek isteyen geliştiriciler için hazırlanmıştır.
>
> **Gereksinimler:** Python 3.9+, harici bağımlılık yok.

---

## İçindekiler

1. [Sistemlere Genel Bakış](#1-sistemlere-genel-bakış)
2. [Kurulum](#2-kurulum)
3. [Entegrasyon Mimarisi](#3-entegrasyon-mimarisi)
4. [Adım Adım Entegrasyon](#4-adım-adım-entegrasyon)
5. [Her Modülün Detaylı Kullanımı](#5-her-modülün-detaylı-kullanımı)
6. [Birleşik Kullanım Örneği](#6-birleşik-kullanım-örneği)
7. [Sistem Entegrasyonu Tam Sorgu Döngüsü](#7-sistem-entegrasyonu-tam-sorgu-döngüsü)
8. [API Referansı](#8-api-referansı)
9. [Sorun Giderme](#9-sorun-giderme)

---

## 1. Sistemlere Genel Bakış

VIGIL ve THE ARC, bir AI asistanının **farkındalık katmanlarını** oluşturur:

```
┌─────────────────────────────────────────────────────────────┐
│  Katman 1 — Narrative (THE ARC)                              │
│  → Kullanıcı nereye gidiyor? Hangi kararlar alındı?          │
│    Hangi konular tekrar gündeme geliyor?                     │
├─────────────────────────────────────────────────────────────┤
│  Katman 2 — User State (TideStone)                           │
│  → Kullanıcı şu an ne hissediyor? Enerjisi yüksek mi?        │
│    Odaklanmış mı?                                            │
├─────────────────────────────────────────────────────────────┤
│  Katman 3 — Goals (CompassStone)                             │
│  → Kullanıcının hedefleri neler? İlerleme kaydedildi mi?     │
├─────────────────────────────────────────────────────────────┤
│  Katman 4 — Recurrence (EmberStone)                          │
│  → Kullanıcı hangi konulari sürekli döndürüyor?              │
│    Sıcak konular hangileri?                                  │
├─────────────────────────────────────────────────────────────┤
│  Katman 5 — Self-Awareness (MirrorStone)                     │
│  → Asistan bu konuda kendine ne kadar güveniyor?             │
│    Hedge dil kullanıyor mu?                                  │
└─────────────────────────────────────────────────────────────┘
```

### Her Modülün Amacı

| Modül | Geliştirici Adı | Amacı |
|-------|----------------|-------|
| **THE ARC** | Long-Term Narrative Tracker | Uzun vadeli konuşma hikayesi: kararlar, ghost thread'ler, büyüme izi |
| **TideStone** | Real-Time User State Reader | Kullanıcının anlık enerji/odak/hız durumu |
| **CompassStone** | Multi-Turn Goal Tracker | Çoklu-sorgu hedef takibi |
| **EmberStone** | Recurring Topic Heat Tracker | Tekrar eden konuların "ısı" takibi |
| **MirrorStone** | Self-Confidence Tracker | Asistanın kendine güveni ve hedge takibi |

---

## 2. Kurulum

### 2.1 Dosyaları Projeye Kopyalama

Tüm modüller tek klasörde toplanır. Önerilen yapı:

```
my_ai_project/
├── vigilstones/           # ← Yeni klasör
│   ├── the_arc.py
│   ├── tide_stone.py
│   ├── compass_stone.py
│   ├── ember_stone.py
│   ├── mirror_stone.py
│   └── signals_vigil.py   # (opsiyonel)
├── your_assistant.py       # ← Kendi asistan dosyanız
├── system_prompt.py
└── main.py
```

### 2.2 Doğrudan Kopyalama

Her dosyayı `Github/` klasöründen `my_ai_project/vigilstones/` klasörüne kopyalayın:

- `the_arc.py`
- `tide_stone.py`
- `compass_stone.py`
- `ember_stone.py`
- `mirror_stone.py`
- `signals_vigil.py` (opsiyyonel)

### 2.3 Hiçbir Bağımlılık Gerekmiyor

Bu modüller **yalnızca Python standart kütüphanesi** kullanır. `requirements.txt`'nize ekleme yapmanız gerekmez.

```bash
# Hiçbir şey yüklemenize gerek yok
pip install  # Boş bırakabilirsiniz
```

---

## 3. Entegrasyon Mimarisi

### 3.1 Temel Kavram: Sorgu Döngüsu

Her modül iki temel noktada devreye girer:

```
Kullanıcı Mesajı
       │
       ▼
┌──────────────────┐
│  OBSERVE (topla) │  ← Her mesajda çağrılır
│  (absorb/observe) │
└──────────────────┘
       │
       ▼
  ┌─────────┐
  │  LLM    │  ← Asistan yanıtı üretir
  └─────────┘
       │
       ▼
┌──────────────────┐
│  OBSERVE (topla) │  ← Her yanıtta çağrılır
│  (absorb/observe) │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  CONSULT (danış) │  ← Bir sonraki LLM çağrısından ÖNCE
│  (consult/directive)│    tüm bağlamı system prompt'a ekle
└──────────────────┘
```

### 3.2 Her Modülün Çağrılma Zamanı

| Modül | Observe Zamanı | Consult Zamanı |
|-------|----------------|----------------|
| **THE ARC** | Her turn sonunda (`absorb`) | LLM çağrısından ÖNCE (`consult`) |
| **TideStone** | Her kullanıcı mesajında (`observe_user`) | LLM çağrısından ÖNCE (`get_state_directive`) |
| **CompassStone** | Her turn sonunda (`observe`) | LLM çağrısından ÖNCE (`get_goal_directive`) |
| **EmberStone** | Her turn sonunda (`observe`) | LLM çağrısından ÖNCE (`get_active_context`) |
| **MirrorStone** | Her assistant yanıtından SONRA (`observe`) | LLM çağrısından ÖNCE (`get_mirror_directive`) |

---

## 4. Adım Adım Entegrasyon

### 4.1 Adım — Modülleri İçe Aktarma

Kendi asistan dosyanızın başına:

```python
# vigilstones/ klasörünü kullanıyorsanız:
from vigilstones.the_arc import TheArc, TurnRecord
from vigilstones.tide_stone import TideStone
from vigilstones.compass_stone import CompassStone
from vigilstones.ember_stone import EmberStone
from vigilstones.mirror_stone import MirrorStone

# vigilstones/ kullanmıyorsanız (dosyaları ana dizine kopyaladıysanız):
from the_arc import TheArc, TurnRecord
from tide_stone import TideStone
from compass_stone import CompassStone
from ember_stone import EmberStone
from mirror_stone import MirrorStone

import time
```

### 4.2 Adım — Modülleri Başlatma

Asistanınızın `__init__` veya başlatma bölümünde:

```python
class MyAssistant:
    def __init__(self):
        # Tüm VIGIL modüllerini başlat
        self.arc     = TheArc(path=".the_arc.json")
        self.tide    = TideStone()
        self.compass = CompassStone(path=".compass_stone.json")
        self.ember   = EmberStone(path=".ember_stone.json")
        self.mirror  = MirrorStone(path=".mirror_stone.json")

        self._turn_id = 0
```

**Parametreler:**
- `path`: JSON dosyasının kaydedileceği yol (varsayılan: `.the_arc.json` vb.)
- `save_every`: Kaç turn'de bir diske kaydedileceği (bazı modüller)
- `min_turns`: TideStone için minimum gözlem sayısı (varsayılan: 3)

### 4.3 Adım — Observe (Toplama)

Her konuşma turn'inde çağrılır:

```python
def on_user_message(self, user_msg: str):
    self._turn_id += 1
    timestamp = time.time()

    # THE ARC — her turn'i kaydet
    self.arc.absorb(TurnRecord(
        turn_id=self._turn_id,
        role="user",
        content=user_msg,
        timestamp=timestamp,
    ))

    # TideStone — sadece kullanıcı mesajı
    self.tide.observe_user(user_msg)

    # CompassStone — hedef takibi
    self.compass.observe(user_msg, "")

    # EmberStone — sıcak konu takibi
    self.ember.observe(user_msg, "")

    # MirrorStone — gözlem (henüz assistant yanıtı yok, boş bırakılabilir)
    # self.mirror.observe(user_msg, "")  # assistant yanıtıyla çağrılır
```

### 4.4 Adım — Assistant Yanıtı Sonrası Observe

LLM yanıtı üretildikten sonra:

```python
def on_assistant_response(self, user_msg: str, assistant_msg: str):
    self._turn_id += 1
    timestamp = time.time()

    # THE ARC — assistant turn'ini de kaydet
    self.arc.absorb(TurnRecord(
        turn_id=self._turn_id,
        role="assistant",
        content=assistant_msg,
        timestamp=timestamp,
    ))

    # CompassStone — assistant yanıtıyla birlikte
    self.compass.observe(user_msg, assistant_msg)

    # EmberStone — assistant yanıtıyla birlikte
    self.ember.observe(user_msg, assistant_msg)

    # MirrorStone — assistant yanıtı HEMEN burada
    self.mirror.observe(user_msg, assistant_msg)
```

### 4.5 Adım — System Prompt Oluşturma (Consult)

Her LLM çağrısından ÖNCE system prompt'a ekleme yapılır:

```python
def build_system_prompt(self, base_prompt: str, user_msg: str) -> str:
    additions = []

    # THE ARC — konuşma geçmişi bağlamı
    if ctx := self.arc.consult(user_msg):
        additions.append(ctx)

    # TideStone — kullanıcı durumu
    if directive := self.tide.get_state_directive():
        additions.append(directive)

    # CompassStone — hedefler
    if directive := self.compass.get_goal_directive():
        additions.append(directive)

    # EmberStone — sıcak konular
    if ctx := self.ember.get_active_context():
        additions.append(ctx)

    # MirrorStone — asistan güveni
    if directive := self.mirror.get_mirror_directive(user_msg):
        additions.append(directive)

    if additions:
        return base_prompt + "\n\n" + "\n\n".join(additions)
    return base_prompt
```

### 4.6 Adım — LLM Çağrısı

```python
def chat(self, user_msg: str) -> str:
    # 1. Observe (kullanıcı mesajı)
    self.on_user_message(user_msg)

    # 2. System prompt oluştur
    enhanced_prompt = self.build_system_prompt(
        base_prompt="Sen yardımsever bir asistansın.",
        user_msg=user_msg,
    )

    # 3. LLM çağır
    response = self.llm.call(enhanced_prompt, user_msg)

    # 4. Observe (assistant yanıtı)
    self.on_assistant_response(user_msg, response)

    return response
```

---

## 5. Her Modülün Detaylı Kullanımı

### 5.1 THE ARC — Uzun Vadeli Anlatı Takibi

THE ARC, konuşmanın **hikaye boyutunu** izler: kullanıcı nereye gidiyor, hangi kararları aldı, hangi konuları tekrar gündeme getiriyor.

```python
from the_arc import TheArc, TurnRecord

arc = TheArc(path="data/the_arc.json")

# TurnRecord oluştur
record = TurnRecord(
    turn_id=1,
    role="user",
    content="I'll use React Native for the mobile app",
    timestamp=time.time(),
)

# Turn'i THE ARC'a absorb et
arc.absorb(record)

# LLM çağrısından ÖNCE danış
context = arc.consult("React Native")
if context:
    print("THE ARC diyor:", context)

# Karar bağlamını al
decisions = arc.get_decision_context("React Native")

# İstatistikleri al
stats = arc.get_stats()
print(f"Toplam episode: {stats['total_episodes']}")

# Periyodik decay çalıştır (günde bir kez önerilir)
arc.run_decay()
```

**Ne döndürür?**
- `arc.consult(query)` → Episode match'leri varsa directive string, yoksa `""`
- `arc.get_decision_context(query)` → O konuyla ilgili geçmiş kararların özeti
- `arc.get_stats()` → `{total_episodes, active, dormant, archived, total_decisions, ghost_threads_detected, total_turns_tracked}`

**Karar Algılama:** THE ARC otomatik olarak şu kalıpları algılar:
- **DECISION:** "yapacağım", "I decided", "I'll use", "seçtim"
- **PROGRESS:** "tamamladım", "finished", "bitirdim"
- **REVISION:** "fikrimi değiştirdim", "changed my mind", "actually not"
- **FRUSTRATION:** "yapamadım", "failed", "error"
- **QUESTION:** Soru işareti ile biten cümleler

### 5.2 TideStone — Anlık Kullanıcı Durumu

Kullanıcının **nasıl** hissettiğini okur (ne söylediği değil, nasıl söylediği):

```python
from tide_stone import TideStone, TideState

tide = TideStone(min_turns=3)

# Her kullanıcı mesajında
tide.observe_user("Uzun ve detaylı bir soru soruyorum burada...")

# Mevcut durumu al
state = tide.get_state()
# state = None dönebilir (yeterli veri yoksa) — bu NORMAL'dir
# state = TideState(energy="high", pace="measured", focus="sharp", turns=5)

if state:
    print(f"Enerji: {state.energy}, Hız: {state.pace}, Odak: {state.focus}")

# System prompt için directive al
directive = tide.get_state_directive()
# directive = "" (yeterli veri yoksa veya her şey normalse)
# directive = "User seems highly engaged — depth is appropriate."
```

**TideState seviyeleri:**

| Boyut | Yüksek | Normal | Düşük |
|-------|--------|--------|-------|
| **energy** | Uzun + karmaşık mesaj | Normal uzunluk | Kısa + basit |
| **pace** | Hızlı yazma (<5s aralık) | Normal (5-20s) | Yavaş (>20s) |
| **focus** | Karmaşık kelime + tutarlı uzunluk | Normal | Dağınık kelime dağarcığı |

**Önemli:** `get_state()` ilk `min_turns` (varsayılan: 3) gözlemden önce `None` döndürür. Bu bilgi yok demektir — boş noise yapmamak için `""` döndürür.

### 5.3 CompassStone — Hedef Takibi

Kullanıcının **nereye** gitmeye çalıştığını izler:

```python
from compass_stone import CompassStone

compass = CompassStone(path="data/compass_stone.json")

# Her turn'de (kullanıcı + assistant yanıtı birlikte)
compass.observe(
    user_text="I want to learn Python this month",
    ai_text="Great goal! Let's start with the basics.",
)

# Sadece kullanıcı mesajıyla
compass.observe_user("I'm trying to build a web app with Flask")

# Aktif hedefleri al
active_goals = compass.get_active_goals()
for goal in active_goals:
    print(f"- {goal.text} ({goal.status})")

# System prompt directive
directive = compass.get_goal_directive()
# directive = "[COMPASS] User goals:\n  - Learn Python this month (active)"
```

**CompassStone otomatik algılar:**
- "I want to learn/build/create..." kalıpları
- Completion sinyalleri: "tamam", "bitirdim", "finished", "done"
- Blocked sinyalleri: "yapamadım", "olmadı", "failed", "blocked"

### 5.4 EmberStone — Tekrar Eden Konular

Kullanıcının **ne** hakkında sürekli konuştuğunu "ısı" ile ölçer:

```python
from ember_stone import EmberStone

ember = EmberStone(path="data/ember_stone.json")

# Her turn'de
ember.observe(
    user_text="I'm working on async Python",
    ai_text="Async is powerful when used correctly...",
)

ember.observe_user("Tell me more about asyncio")

# Aktif (sıcak) konuların bağlamını al
context = ember.get_active_context()
# context = "" (sıcak konu yoksa)
# context = "[EMBER] Recurring topics:\n  - async python [HOT, 3 mentions, 2d]"

# Tüm embers'i al (inceleme için)
all_embers = ember.get_embers()
for e in all_embers:
    print(f"{e.key}: heat={e.heat:.2f}, mentions={e.mentions}")
```

**Isı Döngüsü:**
```
Konu ilk görüldü          → HEAT = 0.30
Tekrar mention           → HEAT += 0.15 (max 1.00)
5 gün sessizlik           → HEAT -= 0.02/gün
Kullanıcı "tamam" dedi   → HEAT -= 0.30 (resolved)
30 gün sessizlik         → Archived (ghost thread)
```

### 5.5 MirrorStone — Asistan Özgüveni

Asistanın **hangi konularda güvendiğini** ve hedge dil kullanıp kullanmadığını izler:

```python
from mirror_stone import MirrorStone

mirror = MirrorStone(path="data/mirror_stone.json")

# Assistant yanıtından HEMEN SONRA
mirror.observe(
    user_text="How does Python async work?",
    ai_text="I think it uses an event loop... it might be based on coroutines...",
)

# Bir konu hakkında güven tahmini al
result = mirror.estimate_confidence("python async")
print(f"Confidence: {result.score} ({result.flag})")
# result.score = 0.0 - 1.0
# result.flag = "low_data" | "confident" | "uncertain" | "low_confidence"
# result.hedge = "i think" (tespit edilen hedge ifadesi)

# Sistem directive al (güvensizse)
if result.flag in ("uncertain", "low_confidence"):
    directive = mirror.get_mirror_directive("python async")
    # directive = "You're using hedging language (i think) — be more direct."
```

**Hedge İfeleri Algılanır:**
- "I think", "I believe", "probably", "maybe", "perhaps"
- "it seems", "from what I know", "I'm not sure"
- "galiba", "sanırım", "olabilir" (Türkçe)

---

## 6. Birleşik Kullanım Örneği

Tam bir chatbot entegrasyonu:

```python
"""Kendi AI Asistanınıza VIGIL Stones Entegrasyonu"""

import time
from vigilstones.the_arc import TheArc, TurnRecord
from vigilstones.tide_stone import TideStone
from vigilstones.compass_stone import CompassStone
from vigilstones.ember_stone import EmberStone
from vigilstones.mirror_stone import MirrorStone


class VIGILAssistant:
    """VIGIL Stones ile entegre edilmiş basit AI asistan."""

    def __init__(self, data_dir: str = "./data"):
        import os
        os.makedirs(data_dir, exist_ok=True)

        self.arc     = TheArc(path=f"{data_dir}/the_arc.json")
        self.tide    = TideStone(min_turns=3)
        self.compass = CompassStone(path=f"{data_dir}/compass_stone.json")
        self.ember   = EmberStone(path=f"{data_dir}/ember_stone.json")
        self.mirror  = MirrorStone(path=f"{data_dir}/mirror_stone.json")

        self._turn_id = 0
        self.base_prompt = (
            "Sen yardımsever, sabırlı ve bilgili bir AI asistansın."
            "Kullanıcının öğrenme hedeflerine saygı göster."
        )

    # ── Observe (Toplama) ──────────────────────────────────────────

    def _observe_user(self, user_msg: str) -> None:
        self._turn_id += 1
        ts = time.time()

        self.arc.absorb(TurnRecord(
            turn_id=self._turn_id,
            role="user",
            content=user_msg,
            timestamp=ts,
        ))
        self.tide.observe_user(user_msg)
        self.compass.observe(user_msg, "")
        self.ember.observe(user_msg, "")

    def _observe_assistant(self, user_msg: str, assistant_msg: str) -> None:
        self._turn_id += 1
        ts = time.time()

        self.arc.absorb(TurnRecord(
            turn_id=self._turn_id,
            role="assistant",
            content=assistant_msg,
            timestamp=ts,
        ))
        self.compass.observe(user_msg, assistant_msg)
        self.ember.observe(user_msg, assistant_msg)
        self.mirror.observe(user_msg, assistant_msg)

    # ── Consult (Danışma) ─────────────────────────────────────────

    def _consult(self, user_msg: str) -> str:
        """Tüm VIGIL bağlamını topla ve system prompt'a ekle."""
        additions = []

        if ctx := self.arc.consult(user_msg):
            additions.append(ctx)
        if d := self.tide.get_state_directive():
            additions.append(d)
        if d := self.compass.get_goal_directive():
            additions.append(d)
        if d := self.ember.get_active_context():
            additions.append(d)
        if d := self.mirror.get_mirror_directive(user_msg):
            additions.append(d)

        if not additions:
            return self.base_prompt

        return self.base_prompt + "\n\n" + "\n\n".join(additions)

    # ── Ana Döngü ──────────────────────────────────────────────────

    def chat(self, user_msg: str, llm_call_fn) -> str:
        """Kullanıcı mesajını al, LLM çağır, yanıtı döndür."""
        # 1. Kullanıcı turn'ini gözlemle
        self._observe_user(user_msg)

        # 2. System prompt oluştur
        system_prompt = self._consult(user_msg)

        # 3. LLM çağır (kendi LLM fonksiyonunuzu burada kullanın)
        response = llm_call_fn(system_prompt, user_msg)

        # 4. Assistant turn'ini gözlemle
        self._observe_assistant(user_msg, response)

        return response


# ── Kullanım ────────────────────────────────────────────────────

def my_llm_call(system_prompt: str, user_msg: str) -> str:
    """Buraya kendi LLM çağrınızı bağlayın (OpenAI, Gemini, vs.)."""
    # Örnek: return openai.ChatCompletion.create(...)
    return "[LLM yanıtı buraya gelecek]"
```

---

## 7. Sistem Entegrasyonu Tam Sorgu Döngüsü

Aşağıda tipik bir sorgu döngüsünün tam akışı gösterilmektedir:

```
┌─────────────────────────────────────────────────────────────────┐
│  KULLANICI: "I'm learning Python async, it's not working"     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVE (Kullanıcı Turn'i)                                     │
│                                                                 │
│  THE ARC    → absorb(TurnRecord)           [episode oluşur]      │
│  TideStone  → observe_user()              [energy=high]         │
│  CompassStone→ observe()                  [goal: learn async]   │
│  EmberStone → observe()                   [heat=0.30]          │
│  MirrorStone→ (henüz yok)                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CONSULT (System Prompt Hazırlığı)                              │
│                                                                 │
│  THE ARC     consult() → "User mentioned 'async python'..."     │
│  TideStone   get_state_directive() → "User focus is sharp..."   │
│  CompassStone get_goal_directive() → "[COMPASS] User goals:.." │
│  EmberStone  get_active_context() → "[EMBER] Recurring topics:.."│
│  MirrorStone get_mirror_directive() → "" (yeterli veri yok)     │
│                                                                 │
│  System prompt += tüm bunlar                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LLM ÇAĞRISI                                                    │
│                                                                 │
│  OpenAI/Gemini/Groq → Model yanıtı üretir                       │
│                                                                 │
│  "I think async Python uses an event loop... you might want..." │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVE (Assistant Turn'i)                                    │
│                                                                 │
│  THE ARC    → absorb(TurnRecord)                                │
│  CompassStone→ observe()                                        │
│  EmberStone → observe()                                        │
│  MirrorStone→ observe(user, assistant)    [HEDGE algılandı!]  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. API Referansı

### TheArc

```python
TheArc(path=".the_arc.json", decay_per_day=0.005, archive_after_days=30,
       dormant_threshold_days=7, max_episodes=500, max_turns_per_episode=50,
       ghost_threshold_days=30)

# Methods
arc.absorb(turn: TurnRecord) -> list[str]          # Episode ID'leri döndürür
arc.consult(query: str, top_k=3) -> str             # Directive veya ""
arc.get_decision_context(query: str) -> str         # Karar özeti veya ""
arc.get_stats() -> dict                             # İstatistikler
arc.run_decay() -> None                            # Periyodik çağrılmalı
arc.summary() -> dict                              # get_stats() ile aynı
arc.reset() -> None                                # Tüm veriyi temizle
```

### TurnRecord

```python
TurnRecord(turn_id: int, role: str, content: str, timestamp: float)
# role: "user" | "assistant"
# timestamp: time.time()
```

### TideStone

```python
TideStone(min_turns=3, max_window=12)

# Methods
tide.observe_user(user_text: str) -> None
tide.get_state() -> TideState | None
tide.get_state_directive() -> str   # "" = yeterli veri yok veya her şey normal
tide.summary() -> dict
tide.reset() -> None

# TideState
TideState(energy: str, pace: str, focus: str, turns: int)
# energy: "high" | "medium" | "low"
# pace:   "brisk" | "measured" | "relaxed"
# focus:  "sharp" | "normal" | "scattered"
```

### CompassStone

```python
CompassStone(path=".compass_stone.json", save_every=5)

# Methods
compass.observe(user_text: str, ai_text: str = "") -> None
compass.observe_user(user_text: str) -> None
compass.get_goal_directive() -> str
compass.get_active_goals() -> list[Goal]
compass.get_stats() -> dict
compass.summary() -> dict
compass.reset_session() -> None   # Sadece session hedeflerini temizle
compass.reset() -> None           # Tüm hedefleri temizle

# Goal
Goal(id: str, text: str, created_at: float, updated_at: float,
     status: str, steps: list, step_statuses: list,
     priority: float, source: str, mentions: int)
# status: "active" | "completed" | "blocked" | "abandoned"
```

### EmberStone

```python
EmberStone(path=".ember_stone.json", active_threshold=0.25,
           heat_boost=0.15, decay_rate=0.02, save_every=5, max_embers=100)

# Methods
ember.observe(user_text: str, ai_text: str = "") -> None
ember.observe_user(user_text: str) -> None
ember.get_active_context() -> str      # Sıcak konular veya ""
ember.get_embers() -> list[Ember]      # Tüm embers
ember.get_stats() -> dict
ember.summary() -> dict
ember.reset() -> None

# Ember
Ember(key: str, heat: float, first_seen: float, last_seen: float,
      mentions: int, resolved: bool, samples: list[str])
```

### MirrorStone

```python
MirrorStone(path=".mirror_stone.json", save_every=10)

# Methods
mirror.observe(user_text: str, ai_text: str) -> None
mirror.estimate_confidence(query: str) -> ConfidenceResult
mirror.get_mirror_directive(query: str) -> str  # "" = confident
mirror.get_stats() -> dict
mirror.summary() -> dict
mirror.reset() -> None

# ConfidenceResult (NamedTuple)
ConfidenceResult(score: float, flag: str, hedge: str)
# score: 0.0 - 1.0
# flag:  "low_data" | "confident" | "uncertain" | "low_confidence"
# hedge: Algılanan hedge ifadesi veya ""
```

---

## 9. Sorun Giderme

### "ModuleNotFoundError: No module named 'the_arc'"

Modülleri kopyaladığınız klasöre Python path'inin erişmediğinden. Çözüm:

```python
import sys
sys.path.insert(0, "/path/to/vigilstones")
# veya
from vigilstones.the_arc import TheArc
```

### "TideStone.get_state() her zaman None dönüyor"

Normal bir davranış. `min_turns` (varsayılan: 3) gözlem toplanana kadar `None` döner. Bu, yeterli veri yokken gereksiz noise yapmamak için tasarlanmıştır. Bir döngüde en az 3 kez `observe_user()` çağırana kadar bekleyin.

### "THE ARC consult() her zaman boş döndürüyor"

THE ARC, Jaccard benzerliği kullanarak episode match etmeye çalışır. Kullanıcı mesajıyla episode konusu arasında en az %20 kelime örtüşmesi olmalıdır. Çok kısa mesajlar ("tamam", "teşekkürler") normalize edildiğinde boş dönebilir — bu normal.

### "JSON dosyaları diske yazılmıyor"

Dosya yazma izinlerini kontrol edin. `path` parametresiyle belirtilen dizinin mevcut ve yazılabilir olduğundan emin olun:

```python
import os
os.makedirs("./data", exist_ok=True)
arc = TheArc(path="./data/the_arc.json")
```

### "MirrorStone hedge algılamıyor"

MirrorStone `observe()` için hem `user_text` hem de `ai_text` gerektirir. Assistant yanıtı olmadan çağrıldığında algılama yapılamaz. `observe()` çağrısını assistant yanıtı üretildikten **hemen sonra** yapın.

### Bellek sızıntısı şüphesi

Tüm modüller `reset()` metodu sunar. Uzun süreli kullanımda periyodik olarak çağırabilirsiniz:

```python
# Her 1000 turn'de bir veya her session başında
arc.reset()
tide.reset()
compass.reset()
ember.reset()
mirror.reset()
```

### Periyodik Bakım

Günde bir kez (veya session başına) `run_decay()` çağrılması önerilir:

```python
import schedule

def daily_decay():
    arc.run_decay()   # THE ARC temperature decay

schedule.every().day.do(daily_decay)
```

---

## Dosya Yapısı (Github Klasörü)

```
Github/
├── the_arc.py          THE ARC — Uzun Vadeli Anlatı Takibi
├── tide_stone.py       TideStone — Anlık Kullanıcı Durumu
├── compass_stone.py    CompassStone — Hedef Takibi
├── ember_stone.py       EmberStone — Tekrar Eden Konu Isı Takibi
├── mirror_stone.py      MirrorStone — Asistan Özgüven Takibi
├── signals_vigil.py    VIGIL Sinyal Setleri (EN + TR)
├── example.py          Tüm modüllerin kullanım örnekleri
├── README.md           Teknik dökümantasyon
└── INSTALLATION_GUIDE.md  Bu dosya
```

---

*Bu rehber VIGIL Stones v1.0 için hazırlanmıştır. Tüm modüller AI asistan FRIDAY'ın içinden çıkarılarak bağımsız hale getirilmiştir.*
