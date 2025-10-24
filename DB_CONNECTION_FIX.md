# 🔧 إصلاح خطأ Database Connection

## المشكلة

```
django.utils.connection.ConnectionDoesNotExist: The connection 'tenant_testc' doesn't exist.
```

### السبب

عندما يحاول المستخدم تسجيل الدخول لـ tenant، يقوم `authentication.py` بمحاولة الاتصال بـ `tenant_testc` database، ولكن هذه الـ database غير مُسجلة في `settings.DATABASES`.

---

## ✅ الحلول المُنفذة

### 1. تحسين `get_tenant_db_config()` - نسخ كامل للإعدادات

**الملف:** `hr_management/tenant_db_router.py`

#### قبل:
```python
def get_tenant_db_config(subdomain, base_config=None):
    if base_config is None:
        base_config = settings.DATABASES['default']
    
    engine = base_config.get('ENGINE', '')
    
    if 'sqlite' in engine:
        config = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': f'tenant_{subdomain}.sqlite3',
        }
    # ...
```

**المشكلة:** ناقص مفاتيح مطلوبة مثل `TIME_ZONE`, `CONN_HEALTH_CHECKS`, إلخ.

#### بعد:
```python
def get_tenant_db_config(subdomain, base_config=None):
    if base_config is None:
        base_config = settings.DATABASES['default'].copy()
    
    # Copy all settings from base config
    config = base_config.copy()
    
    # Override database name based on engine
    engine = config.get('ENGINE', '')
    
    if 'postgresql' in engine:
        config['NAME'] = f'tenant_{subdomain}'
    elif 'mysql' in engine:
        config['NAME'] = f'tenant_{subdomain}'
    elif 'sqlite' in engine:
        config['NAME'] = f'tenant_{subdomain}.sqlite3'
    
    return config
```

**الفائدة:** 
- ✅ ينسخ **جميع** الإعدادات من default DB
- ✅ يتضمن `TIME_ZONE`, `CONN_HEALTH_CHECKS`, `ATOMIC_REQUESTS`، إلخ.
- ✅ يغير فقط اسم Database

---

### 2. تحسين `_register_tenant_database()` - إغلاق اتصالات قديمة

**الملف:** `hr_management/tenant_service.py`

#### قبل:
```python
def _register_tenant_database(subdomain):
    db_alias = f"tenant_{subdomain}"
    db_config = get_tenant_db_config(subdomain)
    
    settings.DATABASES[db_alias] = db_config
    connections.databases[db_alias] = db_config
    
    logger.info(f"✓ Database registered: {db_alias}")
```

**المشكلة:** الاتصال القديم يبقى في الذاكرة

#### بعد:
```python
def _register_tenant_database(subdomain):
    db_alias = f"tenant_{subdomain}"
    db_config = get_tenant_db_config(subdomain)
    
    settings.DATABASES[db_alias] = db_config
    connections.databases[db_alias] = db_config
    
    # If connection already exists, close and remove it
    if db_alias in connections:
        try:
            connections[db_alias].close()
        except:
            pass
        delattr(connections._connections, db_alias)
    
    logger.info(f"✓ Database registered: {db_alias}")
```

**الفائدة:**
- ✅ يغلق الاتصال القديم
- ✅ يحذف الاتصال من cache
- ✅ يضمن اتصال جديد نظيف

---

### 3. إضافة Dynamic Registration في `authentication.py`

**الملف:** `hr_management/authentication.py`

```python
# في validate() method
db_alias = f"tenant_{tenant.subdomain}"

# Ensure database connection is registered
if db_alias not in settings.DATABASES:
    logger.info(f"Database {db_alias} not registered, registering now...")
    db_config = get_tenant_db_config(tenant.subdomain)
    settings.DATABASES[db_alias] = db_config
    # Force connection to be reloaded
    if db_alias in connections:
        del connections[db_alias]

# For SQLite, check if database file exists
if 'sqlite' in settings.DATABASES.get(db_alias, {}).get('ENGINE', ''):
    db_path = settings.DATABASES[db_alias]['NAME']
    if not os.path.isabs(db_path):
        db_path = os.path.join(settings.BASE_DIR, db_path)
    
    if not os.path.exists(db_path):
        raise serializers.ValidationError({
            'error': 'Tenant database not initialized',
            'detail': f'Please contact administrator to setup {tenant.name}'
        })
```

**الفائدة:**
- ✅ يسجل DB ديناميكياً إذا لم يكن مُسجلاً
- ✅ يتحقق من وجود ملف SQLite
- ✅ يعطي رسالة خطأ واضحة للمستخدم

---

### 4. إضافة `--run-syncdb` لـ migrations

**الملف:** `hr_management/tenant_service.py`

```python
def migrate_tenant_database(tenant):
    db_alias = f"tenant_{tenant.subdomain}"
    
    try:
        # Run migrations with --run-syncdb to create all tables
        call_command('migrate', '--run-syncdb', database=db_alias, verbosity=0)
        
        return True, None
    except Exception as e:
        return False, f"Migration error: {str(e)}"
```

**الفائدة:**
- ✅ ينشئ جميع الجداول بدون أخطاء
- ✅ يتجاوز مشكلة "table already exists"

---

## 🧪 الاختبار

### 1. إنشاء tenant جديد

```bash
python manage.py setup_tenant testc --admin-password admin123
```

**النتيجة المتوقعة:**
```
✓ Database Created
✓ Migrations Run  
✓ Superuser Created
✓ Modules Initialized
```

### 2. التحقق من Database

```bash
ls -la tenant_testc.sqlite3
sqlite3 tenant_testc.sqlite3 ".tables"
```

**النتيجة المتوقعة:**
```
-rw-r--r-- 1 user user 733184 Oct 22 14:58 tenant_testc.sqlite3

auth_user
hr_management_employee
hr_management_attendance
...
```

### 3. اختبار Authentication

```bash
# شغّل server أولاً
python manage.py runserver

# في terminal آخر
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Subdomain: testc" \
  -d '{"username":"admin","password":"admin123"}'
```

**النتيجة المتوقعة:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "tenant": "testc",
  "tenant_name": "testc",
  "user_id": 1,
  "username": "admin"
}
```

---

## 📝 ملاحظات مهمة

### 1. Database Registration يحدث في 3 أماكن:

| المكان | متى | الغرض |
|--------|-----|-------|
| `create_tenant_database()` | عند إنشاء tenant | تسجيل DB بعد إنشائه |
| `setup_tenant command` | عند تشغيل command | يستدعي create_tenant_database |
| `authentication.py validate()` | عند login | تسجيل ديناميكي إذا لزم الأمر |

### 2. SQLite Database Files

```
project/
├── db.sqlite3                    # Metadata فقط
├── tenant_testc.sqlite3         # بيانات testc
├── tenant_demo.sqlite3          # بيانات demo
└── tenant_mycompany.sqlite3     # بيانات mycompany
```

### 3. Config Copying مهم جداً

```python
# ❌ خطأ - ناقص إعدادات
config = {'ENGINE': '...', 'NAME': '...'}

# ✅ صحيح - نسخ كامل
config = base_config.copy()
config['NAME'] = f'tenant_{subdomain}'
```

---

## 🐛 استكشاف الأخطاء

### خطأ: "KeyError: 'TIME_ZONE'"

**السبب:** database config ناقص  
**الحل:** استخدم `.copy()` لنسخ كل الإعدادات

### خطأ: "table already exists"

**السبب:** محاولة تشغيل migrations على DB موجود  
**الحل:** استخدم `--run-syncdb` أو احذف DB وأعد إنشاءه

### خطأ: "ConnectionDoesNotExist"

**السبب:** DB غير مُسجل في settings  
**الحل:** استخدم Dynamic Registration في authentication.py

---

## ✅ التغييرات المُنفذة

1. ✅ `tenant_db_router.py` - تحسين `get_tenant_db_config()`
2. ✅ `tenant_service.py` - تحسين `_register_tenant_database()`
3. ✅ `tenant_service.py` - إضافة `--run-syncdb`
4. ✅ `authentication.py` - إضافة Dynamic Registration
5. ✅ `authentication.py` - التحقق من وجود SQLite file

---

**التاريخ:** October 22, 2025  
**الحالة:** ✅ مُصلح ومُختبر  
**الملفات المُعدلة:** 3 ملفات
