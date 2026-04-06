# Mathematical Model of Cryptographic Overhead (Section 2)

> Formalization of encryption impact on industrial communication cycle integrity.

## Per-Packet Processing Time

The time to encrypt/decrypt a single packet for a chosen algorithm:

$$T_{sec} = \frac{P}{V_{alg}} \quad (1)$$

where:
- $P$ — payload size (bytes)
- $V_{alg}$ — measured algorithm throughput (bytes/s)

## Cycle Overhead

Percentage overhead relative to the protocol cycle budget:

$$\eta = \frac{T_{sec}}{T_{cyc}} \times 100\% \quad (2)$$

where $T_{cyc}$ — target cycle time of the protocol (see Table 1 in the paper).

## Total Control Loop Latency

Total latency of a control loop with security overhead:

$$T_{total} = T_{comm} + N \cdot T_{sec} + T_{proc} \quad (3)$$

where:
- $T_{comm}$ — base communication latency
- $N$ — number of nodes in the chain
- $T_{proc}$ — control logic processing time

## Stability Criterion

The system remains deterministic if and only if:

$$T_{total} \leq T_{cyc} \quad (4)$$

## Reference Protocol Parameters

| Protocol | Target Cycle ($T_{cyc}$), µs | Typical Payload, Bytes | Hierarchy Level |
|---|---|---|---|
| EtherCAT | 100 | 64 | Field (Hard Real-Time) |
| PROFINET IRT | 250 | 128 | Control (Hard Real-Time) |
| Modbus TCP | 50,000 | 252 | Control / Operational |
| OPC UA | 100,000 | 1,024 | Management (Secure) |
| MQTT + TLS | 200,000 | 1,024 | Cloud / Management |
