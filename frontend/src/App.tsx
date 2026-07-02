import { useEffect, useState } from "react";

interface Account {
  id: number;
  name: string;
  balance: number;
}

export default function App() {
  const [backendStatus, setBackendStatus] = useState("checking...");
  const [accounts, setAccounts] = useState<Account[]>([]);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => response.json())
      .then((body) => setBackendStatus(body.status))
      .catch(() => setBackendStatus("unreachable"));

    fetch("/api/accounts")
      .then((response) => response.json())
      .then((body) => setAccounts(body.accounts))
      .catch(() => setAccounts([]));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>Ignite</h1>
      <p>Personal finance — scaffold.</p>
      <p>
        Backend status: <strong>{backendStatus}</strong>
      </p>
      <h2>Accounts</h2>
      <ul>
        {accounts.map((account) => (
          <li key={account.id}>
            {account.name}: ${account.balance.toFixed(2)}
          </li>
        ))}
      </ul>
    </main>
  );
}
