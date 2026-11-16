# -*- coding: utf-8 -*-
"""
رجیستری قابلیت‌های هوش مصنوعی
==============================
هر «نقطه AI» کاتالوگ را به یک موتور هوش مصنوعی مشخص نگاشت می‌کند تا
ژنراتور بتواند برای هر موتور:

  * روتر و اندپوینت FastAPI در میکروسرویس پایتون بسازد
  * کلاس سرویس و کلاینت در بک‌اند لاراول تولید کند
  * ویجت هوشمند در فرانت‌اند ری‌اکت ایجاد کند
  * وابستگی‌های pip و متغیرهای محیطی لازم را درج کند

موتورها بر پایه الگوریتم دسته‌بندی شده‌اند، نه بر پایه ماژول؛ بنابراین
یک موتور (مثلاً «پیش‌بینی سری زمانی») می‌تواند ده‌ها نقطه AI در بخش‌های
مختلف را پوشش دهد و کد تکراری تولید نشود.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..catalog.registry import ai_points, index


@dataclass(frozen=True)
class Engine:
    """تعریف یک موتور هوش مصنوعی."""

    key: str
    name_fa: str
    name_en: str
    category: str
    algorithms: list[str]
    pip_packages: list[str]
    model_dir: str
    endpoint: str
    inputs: list[str]
    outputs: list[str]
    description: str
    uses_llm: bool = False          # قابلیت استفاده از AvalAI (LLM)
    realtime: bool = False          # اجرای بلادرنگ / جریان داده
    retraining: str = "weekly"      # زمان‌بندی بازآموزی
    metrics: list[str] = field(default_factory=lambda: ["دقت مدل", "زمان پاسخ"])


ENGINES: dict[str, Engine] = {
    "forecasting": Engine(
        key="forecasting",
        name_fa="موتور پیش‌بینی سری زمانی",
        name_en="Time-Series Forecasting",
        category="prediction",
        algorithms=["Prophet", "XGBoost", "LSTM", "SARIMA", "Exponential Smoothing"],
        pip_packages=["pandas", "numpy", "scikit-learn", "xgboost", "statsmodels", "prophet"],
        model_dir="models/forecasting",
        endpoint="/api/ai/forecast",
        inputs=["سری زمانی تاریخی", "تقویم و فصلی بودن", "متغیرهای بیرونی"],
        outputs=["پیش‌بینی چند دوره‌ای", "بازه اطمینان", "اهمیت متغیرها"],
        description="پیش‌بینی تقاضا، فروش، قیمت، مصرف انرژی و زمان تحویل با مدل‌های آماری و یادگیری عمیق.",
        retraining="weekly",
        metrics=["MAPE", "RMSE", "MAE", "پوشش بازه اطمینان"],
    ),
    "reliability": Engine(
        key="reliability",
        name_fa="موتور قابلیت اطمینان و RUL",
        name_en="Reliability & Remaining Useful Life",
        category="prediction",
        algorithms=["Weibull Analysis", "Cox Proportional Hazards", "Random Survival Forest", "LSTM-RUL"],
        pip_packages=["lifelines", "scikit-learn", "numpy", "pandas"],
        model_dir="models/reliability",
        endpoint="/api/ai/reliability",
        inputs=["تاریخچه خرابی تجهیزات", "داده سنسوری", "ساعت کارکرد"],
        outputs=["عمر مفید باقیمانده", "احتمال خرابی در افق زمانی", "پارامترهای توزیع عمر"],
        description="پیش‌بینی خرابی تجهیزات، محاسبه RUL و مدل‌سازی توزیع عمر برای نگهداری پیش‌بینانه.",
        retraining="daily",
        metrics=["C-index", "خطای RUL", "دقت هشدار زودهنگام"],
    ),
    "optimization": Engine(
        key="optimization",
        name_fa="موتور بهینه‌سازی",
        name_en="Optimization Engine",
        category="prescriptive",
        algorithms=["Genetic Algorithm", "Simulated Annealing", "MILP", "OR-Tools CP-SAT", "Greedy Heuristics"],
        pip_packages=["ortools", "scipy", "numpy", "pandas"],
        model_dir="models/optimization",
        endpoint="/api/ai/optimize",
        inputs=["محدودیت‌ها", "تابع هدف", "داده منابع و سفارشات"],
        outputs="برنامه بهینه، توالی پیشنهادی، تخصیص منابع، تحلیل حساسیت",
        description="بهینه‌سازی زمان‌بندی تولید، موجودی، مسیر، انرژی و تخصیص منابع با روش‌های دقیق و فراابتکاری.",
        retraining="on-demand",
        metrics=["بهبود تابع هدف", "زمان حل", "نرخ تحقق محدودیت‌ها"],
    ),
    "anomaly": Engine(
        key="anomaly",
        name_fa="موتور تشخیص ناهنجاری",
        name_en="Anomaly Detection",
        category="detection",
        algorithms=["Isolation Forest", "One-Class SVM", "Autoencoder", "Z-Score / IQR", "LOF"],
        pip_packages=["scikit-learn", "numpy", "pandas"],
        model_dir="models/anomaly",
        endpoint="/api/ai/anomaly",
        inputs=["داده تراکنشی یا سنسوری", "پنجره زمانی", "آستانه حساسیت"],
        outputs=["امتیاز ناهنجاری", "پرچم رکوردهای مشکوک", "توضیح ویژگی‌های مؤثر"],
        description="تشخیص ناهنجاری در فرآیند تولید، تراکنش‌های مالی، رفتار کاربران و داده سنسورها.",
        realtime=True,
        retraining="daily",
        metrics=["دقت هشدار", "مثبت کاذب", "زمان تشخیص"],
    ),
    "computer_vision": Engine(
        key="computer_vision",
        name_fa="موتور بینایی ماشین",
        name_en="Computer Vision",
        category="perception",
        algorithms=["YOLOv8", "ResNet Transfer Learning", "OpenCV Classical Pipeline", "Tesseract OCR"],
        pip_packages=["opencv-python-headless", "ultralytics", "torch", "torchvision", "pillow", "pytesseract"],
        model_dir="models/vision",
        endpoint="/api/ai/vision",
        inputs=["تصویر یا جریان ویدیو", "کلاس‌های هدف", "آستانه اطمینان"],
        outputs=["جعبه‌های تشخیص", "کلاس و امتیاز", "تصویر نشانه‌گذاری‌شده", "متن استخراج‌شده"],
        description="بازرسی بصری کیفیت، شمارش اشیا، OCR و تشخیص انطباق ایمنی (PPE).",
        realtime=True,
        retraining="monthly",
        metrics=["mAP", "دقت تشخیص عیب", "تأخیر هر فریم"],
    ),
    "nlp": Engine(
        key="nlp",
        name_fa="موتور پردازش زبان طبیعی",
        name_en="Natural Language Processing",
        category="language",
        algorithms=["Transformers (BERT/ParsBERT)", "Keyword Extraction", "Embedding Similarity", "LLM via AvalAI"],
        pip_packages=["transformers", "torch", "hazm", "sentence-transformers", "httpx"],
        model_dir="models/nlp",
        endpoint="/api/ai/nlp",
        inputs=["متن ورودی فارسی", "نوع وظیفه", "زمینه کاری"],
        outputs=["دسته‌بندی", "احساسات", "خلاصه", "پاسخ تولیدشده", "نهفته معنایی"],
        description="چت‌بات، درک و خلاصه‌سازی اسناد، تحلیل احساسات و طبقه‌بندی خودکار متن فارسی.",
        uses_llm=True,
        retraining="monthly",
        metrics=["F1 دسته‌بندی", "امتیاز کیفیت پاسخ", "زمان پاسخ"],
    ),
    "recommendation": Engine(
        key="recommendation",
        name_fa="موتور توصیه‌گر",
        name_en="Recommendation Engine",
        category="prescriptive",
        algorithms=["Matrix Factorization", "KNN Collaborative Filtering", "Gradient Boosting Ranker", "Content-based"],
        pip_packages=["scikit-learn", "implicit", "numpy", "pandas"],
        model_dir="models/recommendation",
        endpoint="/api/ai/recommend",
        inputs=["تاریخچه تعاملات", "ویژگی آیتم‌ها", "زمینه کاربر"],
        outputs=["فهرست پیشنهادها با امتیاز", "دلیل پیشنهاد"],
        description="پیشنهاد محصول، تأمین‌کننده، اقدام بعدی و دانش مرتبط به کاربران.",
        retraining="daily",
        metrics=["Precision@K", "Recall@K", "نرخ پذیرش پیشنهاد"],
    ),
    "quality_spc": Engine(
        key="quality_spc",
        name_fa="موتور کنترل آماری کیفیت",
        name_en="Statistical Quality Intelligence",
        category="analytics",
        algorithms=["Nelson Rules", "EWMA/CUSUM", "Capability Indices", "Random Forest Defect Root-Cause", "ANOVA"],
        pip_packages=["numpy", "pandas", "scipy", "scikit-learn", "statsmodels"],
        model_dir="models/quality",
        endpoint="/api/ai/quality",
        inputs=["داده اندازه‌گیری فرآیند", "حدود مشخصه", "پارامترهای ماشین"],
        outputs=["نقض قواعد کنترل", "پیش‌بینی Cpk", "علل اصلی ضایعات"],
        description="تشخیص الگوهای غیرتصادفی، پیش‌بینی قابلیت فرآیند و ریشه‌یابی خودکار ضایعات.",
        realtime=True,
        retraining="weekly",
        metrics=["نرخ تشخیص الگو", "دقت ریشه‌یابی", "پوشش هشدار"],
    ),
    "classification": Engine(
        key="classification",
        name_fa="موتور طبقه‌بندی و امتیازدهی",
        name_en="Classification & Scoring",
        category="analytics",
        algorithms=["XGBoost", "Logistic Regression", "Random Forest", "ABC/XYZ Segmentation"],
        pip_packages=["scikit-learn", "xgboost", "pandas", "numpy"],
        model_dir="models/classification",
        endpoint="/api/ai/classify",
        inputs=["ویژگی‌های رکورد", "برچسب‌های تاریخی"],
        outputs=["کلاس پیش‌بینی‌شده", "امتیاز ریسک", "اهمیت ویژگی‌ها"],
        description="امتیازدهی اعتبار مشتری، رتبه‌بندی تأمین‌کننده، غربالگری رزومه و دسته‌بندی اسناد.",
        retraining="weekly",
        metrics=["AUC", "F1", "دقت رتبه‌بندی"],
    ),
    "simulation": Engine(
        key="simulation",
        name_fa="موتور شبیه‌سازی و دوقلوی دیجیتال",
        name_en="Simulation & Digital Twin",
        category="prescriptive",
        algorithms=["Discrete Event Simulation", "Monte Carlo", "Agent-based Simulation"],
        pip_packages=["simpy", "numpy", "pandas"],
        model_dir="models/simulation",
        endpoint="/api/ai/simulate",
        inputs=["مدل فرآیند", "توزیع‌های ورودی", "سناریوها"],
        outputs=["نتایج سناریو", "توزیع خروجی‌ها", "تنگناها"],
        description="شبیه‌سازی سناریوهای تولید، شبکه توزیع، بحران و تحلیل چه‌اگر.",
        retraining="on-demand",
        metrics=["اعتبار مدل", "زمان شبیه‌سازی", "حساسیت خروجی"],
    ),
    "mlops": Engine(
        key="mlops",
        name_fa="مدیریت چرخه عمر مدل",
        name_en="MLOps & Model Monitoring",
        category="platform",
        algorithms=["Feature Store", "Drift Detection (PSI/KS)", "AutoML Pipeline", "Model Registry"],
        pip_packages=["scikit-learn", "evidently", "mlflow", "numpy", "pandas"],
        model_dir="models/mlops",
        endpoint="/api/ai/mlops",
        inputs=["داده آموزش", "داده عملیاتی", "متادیتای مدل"],
        outputs=["وضعیت مدل", "هشدار دریفت", "نسخه مدل منتشرشده"],
        description="مهندسی ویژگی، آموزش خودکار، ثبت نسخه، پایش دریفت و آزمون A/B مدل‌ها.",
        retraining="scheduled",
        metrics=["دریفت داده", "افت دقت مدل", "زمان بازآموزی"],
    ),
}


# --------------------------------------------------------------------------- #
# قواعد دسته‌بندی نقطه AI به موتور
# --------------------------------------------------------------------------- #
KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("computer_vision", ("بینایی ماشین", "تصویر", "دوربین", "ocr", "نویسه", "عیوب ظاهری", "تشخیص چهره",
                         "پلاک", "لحیم", "aoi", "چهره")),
    ("nlp", ("زبان طبیعی", "چت‌بات", "دستیار", "متن", "خلاصه", "احساسات", "صوت", "گفتار", "صورتجلسه",
             "مکاتبات", "قرارداد", "استخراج بند", "پرسش", "جست‌وجوی معنایی", "nlq", "دانش مرتبط",
             "طبقه‌بندی خودکار اسناد")),
    ("quality_spc", ("cpk", "نلسون", "الگوهای غیرتصادفی", "ضایعات", "ریشه‌یابی", "قابلیت فرآیند",
                     "نتایج آزمون", "بازده", "عیوب")),
    ("reliability", ("rul", "عمر مفید", "خرابی", "وایبول", "توقف", "ارتعاش", "روغن", "سنسور",
                     "دریفت سنسور", "قابلیت اطمینان", "پیش‌بینی خرابی")),
    ("anomaly", ("ناهنجاری", "مشکوک", "غیرعادی", "تقلب", "نفوذ", "رفتار کاربر", "انحراف از برنامه",
                 "ناهنجار", "هزاره")),
    ("optimization", ("بهینه", "بالانس", "توالی", "زمان‌بندی", "تخصیص", "مسیر", "چیدمان", "سبد خرید",
                      "موجودی ایمنی", "اختلاط", "برش", "شیفت", "کاهش هزینه")),
    ("simulation", ("شبیه‌سازی", "سناریو", "دوقلو", "چه‌اگر", "what-if", "مونت‌کارلو", "بحران")),
    ("recommendation", ("پیشنهاد", "توصیه", "اقدام بعدی", "فروش متقاطع", "شخصی‌سازی", "بنچمارک حقوق")),
    ("forecasting", ("پیش‌بینی", "forecast", "پیش‌بینانه", "روند", "آینده", "تخمین", "پیش‌نگری",
                     "دریفت داده", "دریفت مدل", "کشش قیمتی", "قیمت", "تقاضا", "مصرف انرژی", "ماندگاری")),
    ("classification", ("دسته‌بندی", "طبقه‌بندی", "امتیازدهی", "رتبه‌بندی", "غربالگری", "شناسایی استعداد",
                        "خوشه", "ریسک", "امتیاز")),
    ("mlops", ("mlops", "ویژگی", "feature store", "بازآموزی", "آزمون a/b", "نسخه مدل", "automl",
               "پایش مدل", "دریفت")),
]

# بازنویسی صریح برای پیشوندهای مشخص (دقت بالاتر از قواعد کلیدواژه‌ای)
PREFIX_OVERRIDES: list[tuple[str, str]] = [
    ("K1.", "forecasting"),
    ("K2.", "optimization"),
    ("K3.", "computer_vision"),
    ("K4.", "nlp"),
    ("K5.", "recommendation"),
    ("K6.", "anomaly"),
    ("K7.", "mlops"),
    ("C2.", "reliability"),
    ("B3.", "quality_spc"),
    ("J4.", "simulation"),
]

CODE_OVERRIDES: dict[str, str] = {
    "A1.7.7": "forecasting",
    "A2.7.5": "quality_spc",
    "A3.5.4": "recommendation",
    "A7.2.3": "reliability",
    "C5.1.8": "reliability",
    "C5.2.7": "reliability",
    "D2.2.7": "classification",
    "D2.3.6": "classification",
    "E1.4.5": "classification",
    "E2.1.6": "classification",
    "E2.5.3": "classification",
    "E2.5.5": "recommendation",
    "E6.2.6": "nlp",
    "F1.2.7": "anomaly",
    "F3.2.4": "anomaly",
    "F9.5.6": "classification",
    "G2.2.5": "nlp",
    "G8.4.2": "classification",
    "G12.4.4": "classification",
    "L1.4.1": "nlp",
    "L2.4.1": "nlp",
    "M1.5.2": "computer_vision",
    "P1.3.2": "computer_vision",
    "S1.3.5": "anomaly",
    "S6.3.4": "anomaly",
    "S7.2.4": "nlp",
    "U3.3.2": "nlp",
    "V1.3.1": "forecasting",
}


def engine_for(item_code: str, item_name: str) -> str:
    """موتور متناظر یک نقطه AI را تعیین می‌کند."""
    if item_code in CODE_OVERRIDES:
        return CODE_OVERRIDES[item_code]
    for prefix, engine in PREFIX_OVERRIDES:
        if item_code.startswith(prefix):
            return engine
    lowered = item_name.lower()
    for engine, keywords in KEYWORD_RULES:
        if any(keyword in lowered for keyword in keywords):
            return engine
    return "classification"


def capability_catalog() -> list[dict[str, Any]]:
    """فهرست کامل نقاط AI همراه با موتور متناظر."""
    idx = index()
    result = []
    for point in ai_points():
        engine_key = engine_for(point["code"], point["name"])
        engine = ENGINES[engine_key]
        result.append(
            {
                **point,
                "engine": engine_key,
                "engine_name_fa": engine.name_fa,
                "engine_name_en": engine.name_en,
                "category": engine.category,
                "endpoint": engine.endpoint,
                "algorithms": engine.algorithms,
                "uses_llm": engine.uses_llm,
                "realtime": engine.realtime,
                "retraining": engine.retraining,
                "metrics": engine.metrics,
                "requires_data_from": sorted({d[:2] for d in point["deps"] if d}) or [point["module_code"]],
                "model_id": f"{engine_key}_{point['code'].replace('.', '_').lower()}",
                "feature_flag": f"ai.{engine_key}.{point['code'].lower().replace('.', '_')}",
            }
        )
    return result


def engine_summary(selected_codes: set[str] | None = None) -> list[dict[str, Any]]:
    """خلاصه موتورهای مورد نیاز بر اساس نقاط AI انتخاب‌شده."""
    capabilities = capability_catalog()
    if selected_codes is not None:
        capabilities = [c for c in capabilities if c["code"] in selected_codes]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for cap in capabilities:
        grouped.setdefault(cap["engine"], []).append(cap)

    summary = []
    for engine_key, caps in sorted(grouped.items()):
        engine = ENGINES[engine_key]
        summary.append(
            {
                "engine": engine_key,
                "name_fa": engine.name_fa,
                "name_en": engine.name_en,
                "category": engine.category,
                "endpoint": engine.endpoint,
                "model_dir": engine.model_dir,
                "algorithms": engine.algorithms,
                "pip_packages": engine.pip_packages,
                "uses_llm": engine.uses_llm,
                "realtime": engine.realtime,
                "retraining": engine.retraining,
                "metrics": engine.metrics,
                "inputs": engine.inputs,
                "outputs": engine.outputs if isinstance(engine.outputs, list) else [engine.outputs],
                "description": engine.description,
                "capabilities": [
                    {"code": c["code"], "name": c["name"], "module_code": c["module_code"],
                     "model_id": c["model_id"], "feature_flag": c["feature_flag"]}
                    for c in caps
                ],
                "count": len(caps),
            }
        )
    return summary


def engine_by_key(key: str) -> Engine | None:
    return ENGINES.get(key)
