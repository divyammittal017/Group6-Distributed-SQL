# Group 6 — Distributed SQL / NewSQL experiment

This starter project runs a three-node CockroachDB cluster in Docker and benchmarks
simple ACID update/read transactions before and during a one-node failure.

## Important limitations

- This is a **local development experiment**: three containers share one physical Mac.
- The cluster uses CockroachDB's insecure mode. The published ports are bound to 127.0.0.1
  for localhost coursework only; do not expose this configuration publicly or use it in production.
- Record your Mac model, RAM, macOS version, Docker version, CockroachDB image tag,
  benchmark duration, worker count, and all results in the paper.
- Do not invent or edit benchmark results. Keep the generated CSV files.

## 1. Start the cluster

From this directory:

```bash
docker compose up -d
docker compose ps
```

Wait until all three node containers are running. Then initialize the cluster once:

```bash
docker compose exec node1 cockroach init --insecure --host=node1:26257
```

If it reports that the cluster is already initialized, that is okay.

Check membership:

```bash
docker compose exec node1 cockroach node status --insecure --host=node1:26257
```

You should see three nodes.

## 2. Create the database and test data

```bash
docker compose exec -T node1 cockroach sql --insecure --host=node1:26257 < sql/schema.sql
```

Check the data:

```bash
docker compose exec node1 cockroach sql --insecure --host=node1:26257 --database=distributed_lab -e "SELECT count(*) FROM accounts;"
```

Expected row count: 10000.

## 3. Open the DB Console

- Node 1: http://localhost:8080
- Node 2: http://localhost:8081
- Node 3: http://localhost:8082

## 4. Set up the Python benchmark

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 5. Baseline measurement — all nodes online

Make sure all three nodes are running:

```bash
docker compose ps
```

Run a 60-second workload with four workers:

```bash
python benchmark.py --scenario baseline --duration 60 --workers 4
```

This creates `results/baseline.csv`.

## 6. Failure measurement — stop node 3

In a second terminal:

```bash
docker compose stop node3
```

Confirm that node3 is stopped:

```bash
docker compose ps
```

Run the same workload against node1:

```bash
python benchmark.py --scenario node3_down --duration 60 --workers 4
```

This creates `results/node3_down.csv`.

Do not assume the failure scenario will have zero errors or identical latency. Record what actually happens.

## 7. Restore node 3

```bash
docker compose start node3
```

Wait for it to rejoin, then check:

```bash
docker compose exec node1 cockroach node status --insecure --host=node1:26257
```

## 8. Stop the cluster

Stop containers but preserve data:

```bash
docker compose down
```

To delete the cluster and all its stored data permanently:

```bash
docker compose down -v
```

Use the second command only when you intentionally want a fresh cluster.

## Ports

| Node | Host SQL port | Admin UI |
|---|---:|---|
| node1 | 26257 | 8080 |
| node2 | 26258 | 8081 |
| node3 | 26259 | 8082 |

The benchmark connects to node1 on localhost port 26257 in both scenarios.
