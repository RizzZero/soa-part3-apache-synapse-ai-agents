# مرحله سوم پروژه SOA - معماری Apache Synapse و Agent های هوش مصنوعی

این پروژه شامل سه بخش اصلی است که با کمک Cursor AI پیاده‌سازی شده است:

## 🏗️ بخش 1: معماری ساده Apache Synapse

### فایل: `simple-synapse-architecture.py`

یک نسخه ساده از معماری Apache Synapse ESB که شامل:

- **Message**: ساختار پیام‌ها در ESB
- **Mediator**: کلاس‌های واسط برای پردازش پیام‌ها
  - `LogMediator`: ثبت لاگ پیام‌ها
  - `TransformMediator`: تبدیل و تغییر پیام‌ها
- **Endpoint**: نمایانگر سرویس‌های مقصد
- **Proxy**: سرویس‌های واسط با قابلیت اضافه کردن mediator
- **ESB**: اتوبوس سرویس سازمانی که همه چیز را مدیریت می‌کند

### ویژگی‌ها:
- پردازش پیام‌ها با mediator های مختلف
- مسیریابی پیام‌ها بین proxy ها
- شبیه‌سازی فراخوانی سرویس‌ها

## 🔌 بخش 2: سرویس‌های MCP Server

### فایل: `mcp_servers.py`

دو سرویس MCP (Model Context Protocol) برای تعامل Agent های هوش مصنوعی:

### 1. UserManagementMCPServer
- مدیریت کاربران
- عملیات: `get_user`, `list_users`, `create_user`, `update_user`
- داده‌های نمونه کاربران

### 2. OrderProcessingMCPServer
- پردازش سفارشات
- مدیریت موجودی
- عملیات: `get_order`, `list_orders`, `create_order`, `update_order_status`, `get_inventory`

### ویژگی‌ها:
- پردازش درخواست‌های async
- مدیریت خطاها
- ثبت لاگ عملیات
- مدیر سرویس‌ها برای هماهنگی

## 🤖 بخش 3: Agent های هوش مصنوعی

### فایل: `ai_agents.py`

دو Agent هوش مصنوعی که می‌توانند با هم و با سرویس‌های MCP تعامل کنند:

### 1. UserServiceAgent
- مسئول عملیات مربوط به کاربران
- تخصص: مدیریت کاربران، احراز هویت، مدیریت پروفایل
- عملیات: `get_user_info`, `validate_user`, `create_user_profile`

### 2. OrderServiceAgent
- مسئول عملیات مربوط به سفارشات
- تخصص: پردازش سفارشات، مدیریت موجودی، پردازش پرداخت
- عملیات: `get_order_info`, `create_order`, `validate_order`, `process_payment`

### ویژگی‌های Agent ها:
- حافظه برای ذخیره پیام‌ها
- تاریخچه مکالمات
- فرآیند تفکر (thinking process)
- قابلیت تحلیل و تصمیم‌گیری

## 🎭 سناریوهای تعامل

### AgentOrchestrator
مدیر هماهنگی بین Agent ها و سرویس‌های MCP که شامل:

### سناریو 1: User-Order Integration
1. OrderServiceAgent از UserServiceAgent درخواست اعتبارسنجی کاربر می‌کند
2. در صورت موفقیت، OrderServiceAgent سفارش جدید ایجاد می‌کند
3. OrderServiceAgent پرداخت را پردازش می‌کند

### سناریو 2: Payment Processing
1. UserServiceAgent اطلاعات سفارش را از OrderServiceAgent دریافت می‌کند
2. OrderServiceAgent سفارش را برای پرداخت اعتبارسنجی می‌کند
3. در صورت موفقیت، پرداخت پردازش می‌شود

## 🚀 نحوه اجرا

### پیش‌نیازها:
```bash
pip install asyncio
```

### اجرای تست‌ها:

#### 1. تست معماری Synapse:
```bash
python simple-synapse-architecture.py
```

#### 2. تست سرویس‌های MCP:
```bash
python mcp_servers.py
```

#### 3. تست Agent های هوش مصنوعی:
```bash
python ai_agents.py
```

## 📊 خروجی نمونه

### خروجی Agent ها:
```
=== Scenario Execution Log ===
Time: 2024-01-15T10:30:00
From: OrderServiceAgent -> To: UserServiceAgent
Message: {'operation': 'validate_user', 'data': {'user_id': 'user1'}, 'context': 'order_creation'}
Response: {'operation': 'user_validation_response', 'data': {'user_id': 'user1', 'is_valid': True, 'permissions': ['read', 'write', 'order'], 'message': 'User validation successful'}, 'thoughts': {...}}
--------------------------------------------------
```

## 🔧 ساختار پروژه

```
├── simple-synapse-architecture.py  # معماری Apache Synapse
├── mcp_servers.py                  # سرویس‌های MCP
├── ai_agents.py                    # Agent های هوش مصنوعی
└── README.md                       # مستندات پروژه
```

## 🎯 ویژگی‌های کلیدی

1. **معماری قابل گسترش**: امکان اضافه کردن mediator ها و endpoint های جدید
2. **تعامل هوشمند**: Agent ها می‌توانند تصمیم‌گیری کنند و با هم همکاری کنند
3. **مدیریت خطا**: پردازش خطاها در تمام سطوح
4. **لاگ کامل**: ثبت تمام عملیات برای نظارت و دیباگ
5. **سناریوهای واقعی**: پیاده‌سازی سناریوهای کاربردی

## 🔮 توسعه آینده

- اضافه کردن Agent های بیشتر
- پیاده‌سازی یادگیری ماشین در Agent ها
- اضافه کردن رابط کاربری وب
- پشتیبانی از پروتکل‌های ارتباطی مختلف
- اضافه کردن امنیت و احراز هویت

## 📝 یادداشت‌ها

- این پروژه با کمک Cursor AI توسعه یافته است
- تمام کدها با Python 3.8+ سازگار هستند
- از الگوهای طراحی Object-Oriented استفاده شده است
- کدها کامنت‌گذاری شده و قابل فهم هستند 