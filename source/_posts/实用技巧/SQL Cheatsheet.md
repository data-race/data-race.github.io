---
title: SQL Cheatsheet
tags:
  - cheatsheet
categories:
  - 实用技巧
date: 2023-07-17 20:17:25
---
#cheatsheet 

## 大表查询优化
### 先查id再join
```sql
select a.id, a.project, a.metric_key, a.tag_id, a.tag_value, a.description, a.status
from frontend_tag_value a
join (SELECT id
FROM frontend_tag_value
WHERE project = 'com.sankuai.grocerydt.user.mp'
AND id > 190543649
AND status = 0
ORDER BY id
LIMIT 10000) b
on a.id=b.id
```