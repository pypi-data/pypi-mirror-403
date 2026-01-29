Use real components, mock only external I/O (DB, API, filesystem).

- Unit: `service.process()` calls `repo.save()` with correct args (mock repo)
- Integration: Data actually persists after full flow (real components, fake I/O)
