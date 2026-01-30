
# GNN SDK: Quick Start for Snowflake

### **1. Zip the SDK**
```bash
zip -r relationalai_gnns relationalai_gnns
````

---

### **2. (Optional) Clean old versions**

```sql
USE DATABASE RELATIONAL_AI_GNN;
USE SCHEMA SDK_SCHEMA;

LIST @SDK_STAGE; -- view files
REMOVE @SDK_STAGE/relationalai_gnns.zip; -- delete old package
```

---

### **3. Create a stage (if not exists)**

```sql
CREATE STAGE IF NOT EXISTS MY_PACKAGES;

ALTER SESSION SET query_tag = '{
    "origin":"sf_sit-is",
    "name":"notebook_demo_pack",
    "version":{"major":1,"minor":0},
    "attributes":{"is_quickstart":0,"source":"sql","vignette":"import_package_stage"}
}';
```

---

### **4. Add Snowflake CLI connection**

```bash
snow connection add -n CONNECTION_NAME
```

Fill in:

* **user** = Snowflake username
* **password** = Snowflake password
* **database** = database with stage
* **schema** = schema with stage
* **warehouse** = warehouse name
* **role** = role with write access

---

### **5. Upload the package**

```bash
snow snowpark package upload \
    --connection CONNECTION_NAME \
    --file relationalai_gnns.zip \
    --stage MY_PACKAGES \
    --overwrite
```

---

### **6. Import into Notebook**

* Go to **`Packages`** dropdown → **`Stage Packages`** tab
* Enter:

```
@RELATIONAL_AI_GNN.SDK_SCHEMA.MY_PACKAGES/relationalai_gnns.zip
```

*(replace `RELATIONAL_AI_GNN` and `SDK_SCHEMA` with your actual database & schema)*

---

**Reference:**
[Snowflake Labs — Import Package from Stage](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Import%20Package%20from%20Stage/Import%20Package%20from%20Stage.ipynb)
