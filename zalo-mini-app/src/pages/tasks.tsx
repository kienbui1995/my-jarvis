import React, { useEffect, useState } from "react";
import { Page, Box, Text, Button, useSnackbar } from "zmp-ui";
import { api } from "../api";

type Task = { id: string; title: string; status: string; priority: string; due_date: string | null };

const PRIORITY_ICON: Record<string, string> = { urgent: "🔴", high: "🟠", medium: "🟡", low: "🟢" };

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const { openSnackbar } = useSnackbar();

  const load = () => api.listTasks().then(setTasks).catch(() => openSnackbar({ text: "Lỗi tải tasks" }));
  useEffect(() => { load(); }, []);

  return (
    <Page>
      <Box style={{ padding: 12 }}>
        <Text size="xLarge" bold style={{ marginBottom: 12 }}>📋 Tasks</Text>
        {tasks.length === 0 ? (
          <Text style={{ color: "#888", textAlign: "center", marginTop: 40 }}>Chưa có task nào</Text>
        ) : (
          tasks.map((t) => (
            <Box key={t.id} style={{ background: "#2d2d44", borderRadius: 12, padding: 12, marginBottom: 8 }}>
              <Box flex style={{ justifyContent: "space-between", alignItems: "center" }}>
                <Text bold>{PRIORITY_ICON[t.priority] || "⚪"} {t.title}</Text>
                <Text size="xSmall" style={{ color: t.status === "done" ? "#4CAF50" : "#888" }}>{t.status}</Text>
              </Box>
              {t.due_date && <Text size="xSmall" style={{ color: "#aaa", marginTop: 4 }}>📅 {new Date(t.due_date).toLocaleDateString("vi")}</Text>}
            </Box>
          ))
        )}
      </Box>
    </Page>
  );
}
