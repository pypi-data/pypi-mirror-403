Use real components, mock only external I/O (DB, API, filesystem).

- Unit: `service.Process()` calls `repo.Save()` with correct args (mock repo)
- Integration: Data actually persists after full flow (real components, InMemory implementations)
