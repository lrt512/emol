# Testing Before Cutover

Test the containerized eMoL on port 8080 before switching from your existing installation.

## Workflow

### 1. Deploy on Port 8080

```bash
./deploy-docker.sh --registry <ecr-url> --test
```

This keeps your existing service running on port 80.

### 2. Test

Access `http://your-server:8080` and verify:
- [ ] Authentication works
- [ ] Cards display correctly
- [ ] Admin functions work
- [ ] Static files load
- [ ] No errors in logs

Monitor:
```bash
docker compose -f docker-compose.prod.yml logs -f
docker stats
free -h
```

### 3. Cutover

When ready:
```bash
./deploy-docker.sh --registry <ecr-url> --cutover
```

This stops the old service and switches the container to port 80.

## Rollback

**From test (port 8080):**
```bash
docker compose -f docker-compose.prod.yml down
# Existing service on port 80 continues
```

**From cutover (port 80):**
```bash
docker compose -f docker-compose.prod.yml down
sudo systemctl start emol nginx
```

## Resource Notes

On a 1GB instance, running both services is tight but feasible for brief testing. Monitor `docker stats` and `free -h`. For routine updates, stop the old service first to save memory.
