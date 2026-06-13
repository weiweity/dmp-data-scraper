# DMP 项目功能需求

> 记录用户提出但目前尚未实现的功能
> 格式：FEAT-YYYYMMDD-XXX

---

## [FEAT-20260403-001] 抓取完成后自动同步CSV到frontend目录

**Status**: ❌ closed 2026-06-13 (v0.1.0 彻底独立, frontend 目录不再存在)
**Reason**: Sprint 16 Wave 1 拆出独立 repo 后, 父项目的 frontend/ 目录已不存在。 sync_to_frontend() 函数在 v0.1.8 删除 (dead code 运行时永远 return early)。 当前项目是单纯爬虫, 跟前端看板解耦, 不再需要 CSV 同步。
