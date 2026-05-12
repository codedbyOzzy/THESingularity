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
│  Katman 2 — Intelligence Routing (ORACLE)                     │
│  → Hangi LLM bu turn için en iyisi? (Karmaşıklık vs Maliyet)│
├─────────────────────────────────────────────────────────────┤
│  Katman 3 — User State (TideStone)                           │
│  → Kullanıcı şu an ne hissediyor? Enerjisi yüksek mi?        │
│    Odaklanmış mı?                                            │
├─────────────────────────────────────────────────────────────┤
│  Katman 4 — Goals (CompassStone)                             │
│  → Kullanıcının hedefleri neler? İlerleme kaydedildi mi?     │
├─────────────────────────────────────────────────────────────┤
│  Katman 5 — Recurrence (EmberStone)                          │
│  → Kullanıcı hangi konulari sürekli döndürüyor?              │
│    Sıcak konular hangileri?                                  │
├─────────────────────────────────────────────────────────────┤
│  Katman 6 — Self-Awareness (MirrorStone)                     │
│  → Asistan bu konuda kendine ne kadar güveniyor?             │
│    Hedge dil kullanıyor mu?                                  │
└─────────────────────────────────────────────────────────────┘
```

### Her Modülün Amacı

| Modül | Geliştirici Adı | Amacı |
|-------|----------------|-------|
| **THE ARC** | Long-Term Narrative Tracker | Uzun vadeli konuşma hikayesi: kararlar, ghost thread'ler, büyüme izi |
| **ORACLE** | Intelligent Model Router | Karmaşıklığa göre model seçimi ve maliyet optimizasyonu |
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
│   ├── oracle.py
│   ├── tide_stone.py
│   ├── compass_stone.py
│   ├── ember_stone.py
│   ├── mirror_stone.py
│   └── signals_vigil.py
├── your_assistant.py       # ← Kendi asistan dosyanız
├── system_prompt.py
└── main.py
```

### 2.2 Doğrudan Kopyalama

Her dosyayı `Github/` klasöründen `my_ai_project/vigilstones/` klasörüne kopyalayın.

### 2.3 Hiçbir Bağımlılık Gerekmiyor

Bu modüller **yalnızca Python standart kütüphanesi** kullanır. 

---

## 3. Entegrasyon Mimarisi

### 3.1 Temel Kavram: Sorgu Döngüsu

Her modül iki temel noktada devreye girer: Observe (Topla) ve Consult (Danış).

```python
# 1. Kullanıcı mesajını al
# 2. VIGIL Observe (arc.absorb, tide.observe_user, etc.)
# 3. LLM çağrısından ÖNCE: VIGIL Consult (additions = build_awareness_context())
# 4. LLM Response
# 5. VIGIL Observe Response (mirror.observe, etc.)
```

---

## 6. Birleşik Kullanım Örneği

```python
from the_singularity import TheArc, Oracle, Spectre, Archive

# Başlatma
arc = TheArc()
oracle = Oracle(the_arc=arc)
spectre = Spectre(the_arc=arc)

def chat(user_msg):
    # 1. Karar
    decision = oracle.route(user_msg)
    
    # 2. Tahmin
    preds = spectre.predict_next(arc.get_history())
    
    # 3. Bağlam
    ctx = arc.consult(user_msg)
    
    # ... asistan yanıtı üretimi ...
```

---

## 8. API Referansı

*Detaylı API referansı için modül dosyalarının başındaki docstring'leri inceleyin.*

---

<div align="center">

*"Awareness is not a feature. It is a layer."*

</div>
