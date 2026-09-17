# PostgreSQL 事务、ACID、隔离级别、锁机制
> 适配PostgreSQL，和MySQL InnoDB有不少差异，重点区分MVCC实现、隔离级别行为、锁粒度。

## 一、事务与ACID
**事务**：一组SQL操作，要么全部执行成功，要么全部回滚，是数据库并发控制的基本单位。
### ACID四大特性
1. **原子性 Atomicity**
事务是不可拆分原子单元。`COMMIT`全部生效；`ROLLBACK`全部撤销。
PostgreSQL通过**事务日志WAL（Write Ahead Log）**保障崩溃恢复原子性。
> WAL：写数据前先写日志，宕机后重放日志恢复数据。

2. **一致性 Consistency**
事务执行前后，数据库完整性约束不变（主键、外键、唯一、业务规则）。
原子+隔离+持久化共同保证一致性，不是数据库单独实现。

3. **隔离性 Isolation**
多个并发事务之间相互隔离，一个事务的修改对其他事务可见规则由**隔离级别**控制。
PG依靠**MVCC（多版本并发控制）**实现隔离，不单纯靠锁。

4. **持久性 Durability**
事务提交成功后，修改永久保存，即使服务器宕机也不会丢失。
WAL日志刷盘保证持久化。

> ✅ PG的MVCC核心：**不覆盖旧数据，更新时生成新元组(tuple)，旧版本保留**；每个元组有`xmin`（创建该版本事务ID）、`xmax`（删除/更新该版本事务ID）。旧版本由`VACUUM`清理。

---

## 二、PostgreSQL 事务隔离级别（SQL标准4种，PG只实现3种）
SQL标准：读未提交、读已提交、可重复读、串行化
PG支持：**读已提交（Read Committed）、可重复读（Repeatable Read）、串行化（Serializable）**
> PostgreSQL没有真正的「读未提交」，设置了读未提交实际会降级为**读已提交**。

|隔离级别|脏读|不可重复读|幻读|PG说明|
| ---- | ---- | ---- | ---- | ---- |
|读已提交 Read Committed（默认）|❌禁止|✅允许|✅允许|每次查询取当前快照；同事务内两次同SELECT，可能读到别的事务已提交新数据|
|可重复读 Repeatable Read|❌禁止|❌禁止|❌PG下无幻读|事务启动时创建快照，整个事务内快照不变；**PG的RR比标准RR更强**，规避幻读。但会检测更新冲突，抛出`could not serialize access due to concurrent update`|
|串行化 Serializable|❌禁止|❌禁止|❌禁止|最高隔离，模拟串行执行；PG使用**可序列化快照隔离SSI**，会做冲突检测，发现读写冲突直接报错，需要业务捕获异常重试|

### 三个并发问题定义
1. **脏读**：读到其他事务**未提交**的数据。
2. **不可重复读**：同一个事务内，两次读取同一行，中间被别的事务修改并提交，两次结果不一样。侧重**行数据修改**。
3. **幻读**：同一个事务内，两次范围查询，别的事务插入/删除符合条件数据，行数变化。侧重**新增/删除行**。

> 重点区别MySQL InnoDB RR：MySQL InnoDB RR靠间隙锁解决幻读；PG RR靠MVCC快照，不会加间隙锁，直接在快照层面看不到新插入行。

---

## 三、PostgreSQL 锁机制（表锁 + 行锁）
PG锁分为**表级锁**、**行级锁**，还有轻量的**页锁、元组锁**；MVCC读不加锁（普通SELECT不加行锁）。

### 1. 表级锁（Table Locks）
执行 `LOCK TABLE xxx IN XXX MODE`；DDL操作（ALTER/DROP/TRUNCATE）通常会申请强表锁。
按冲突严格程度从弱到强：
1. **ACCESS SHARE**：SELECT普通查询。只和ACCESS EXCLUSIVE冲突。
2. **ROW SHARE**：SELECT ... FOR SHARE。
3. **ROW EXCLUSIVE**：INSERT / UPDATE / DELETE。
4. **SHARE UPDATE EXCLUSIVE**：VACUUM、CREATE INDEX CONCURRENTLY
5. **SHARE**：CREATE INDEX（非并发）
6. **SHARE ROW EXCLUSIVE**
7. **EXCLUSIVE**
8. **ACCESS EXCLUSIVE**：最强锁。ALTER、DROP、TRUNCATE、LOCK TABLE。**阻塞所有读写**。

> 重点：普通SELECT是ACCESS SHARE，和大部分锁兼容，仅被ACCESS EXCLUSIVE阻塞。

### 2. 行级锁（Row Locks / Tuple Lock）
**行锁不是锁整张表，只锁定被修改的元组**，由DML或`SELECT ... FOR UPDATE/SHARE`触发。
> PG行锁存储在元组头，不是内存单独锁表；MVCC普通SELECT**不获取行锁**。

4种行锁模式：
1. `FOR UPDATE`：排他行锁。其他事务不能改、删、FOR UPDATE；可以普通快照读。
2. `FOR NO KEY UPDATE`：强度弱于FOR UPDATE；更新非主键字段使用。
3. `FOR SHARE`：共享行锁。多个事务可以加SHARE；阻止其他事务UPDATE/DELETE。
4. `FOR KEY SHARE`：最弱共享行锁；主键相关查询。

```sql
-- 排他行锁，锁定查询出来的行，禁止其他事务修改
SELECT * FROM t WHERE id=1 FOR UPDATE;

-- 共享行锁
SELECT * FROM t WHERE id=1 FOR SHARE;
```

#### 锁等待与死锁
- 锁等待：事务申请锁，资源被持有，进入等待队列，可以设置`statement_timeout`、`lock_timeout`。
- 死锁：两个事务互相持有对方需要的锁，PG自动检测死锁，中断其中一个事务抛出错误。

### 3. 重要区分 PG vs MySQL
1. MySQL InnoDB：行锁+间隙锁，RR隔离级别下有间隙锁防幻读；
2. PostgreSQL：**没有间隙锁**。RR隔离级别依靠MVCC快照实现看不到新插入行；串行化SSI才会检测读写冲突。
3. PG读操作默认不加锁，依靠多版本，读写不阻塞；写和写互相阻塞。

## 四、MVCC 简要原理（PG）
1. UPDATE不会原地覆盖旧行，生成新元组，旧元组保留；
2. `xmin`：创建该版本的事务id；`xmax`：删除/更新该版本事务id；
3. 查询时根据事务快照，判断元组版本对当前事务是否可见；
4. 不再被任何事务需要的旧版本，后台`VACUUM`清理回收空间。
> VACUUM不会收缩文件，VACUUM FULL才会，但会锁表。

## 五、常用排查SQL（可直接运行）
```sql
-- 查看当前运行事务、锁等待
SELECT pid, usename, state, wait_event_type, wait_event, query
FROM pg_stat_activity WHERE state <> 'idle';

-- 查看锁信息
SELECT relation::regclass, mode, pid FROM pg_locks;
```

## 六、常见面试要点总结
1. ACID中，隔离性由MVCC+锁实现；持久性由WAL；原子性WAL。
2. PG没有读未提交；RR隔离级别**不存在幻读**，实现方式和MySQL不同。
3. PG普通SELECT不加锁；`SELECT ... FOR UPDATE`才会加行锁。
4. PG没有间隙锁；DDL会拿ACCESS EXCLUSIVE表锁，阻塞所有读写。
5. MVCC旧元组靠VACUUM清理，长时间未提交事务会阻止VACUUM，导致表膨胀。

如果你需要，我可以继续：
方案A：整理成面试问答版（精简背诵）
方案B：写一套可在本地PG运行的事务隔离级别演示SQL脚本，复现脏读、不可重复读、冲突报错
方案C：画文字版MVCC+锁流程图