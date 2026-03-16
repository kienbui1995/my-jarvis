import React, { useEffect, useState } from "react";
import { Page, Box, Text, Input, Button, useSnackbar } from "zmp-ui";
import { api } from "../api";

type Task = { id: string; title: string; status: string; priority: string; due_date: string | null };
const PRIORITY_ICON: Record<string, string> = { urgent: "🔴", high: "🟠", medium: "🟡", low: "🟢" };

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTask, setNewTask] = useState("");
  const { openSnackbar } = useSnackbar();

  const load = () => api.listTasks().then(setTasks).catch(() => openSnackbar({ text: "Lỗi tải tasks" }));
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!newTask.trim()) return;
    await api.createTask(newTask.trim());
    setNewTask("");
    load();
  };

  const toggle = async (t: Task) => {
    const next = t.status === "done" ? "todo" : "done";
    await api.updateTask(t.id, { status: next });
    load();
  };

  return (
    <Page>
      <Box style={{ padding: 12 }}>
        <Text size="xLarge" bold style={{ marginBottom: 12 }}>📋 Tasks</Text>
        <Box flex style={{ gap: 8, marginBottom: 12 }}>
          <Input placeholder="Task mới..." value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            onKeyDown={(e: any) => e.key === "Enter" && add()}
            style={{ flex: 1 }} />
          <Button size="small" onClick={add} disabled={!newTask.trim()}>+</Button>
        </Box>
        {tasks.length === 0 ? (
          <Text style={{ color: "#888", textAlign: "center", marginTop: 40 }}>Chưa có task nào</Text>
        ) : (
          tasks.map((t) => (
            <Box key={t.id} onClick={() => toggle(t)} style={{
              background: t.status === "done" ? "#1a1a2e" : "#2d2d44",
              borderRadius: 12, padding: 12, marginBottom: 8, cursor: "pointer",
              opacity: t.status === "done" ? 0.6 : 1,
            }}>
              <Box flex style={{ justifyContent: "space-between", alignItems: "center" }}>
                <Text bold style={{ textDecoration: t.status === "done" ? "line-through" : "none" }}>
                  {PRIORITY_ICON[t.priority] || "⚪"} {t.title}
                </Text>
                <Text size="xSmall" style={{ color: t.status === "done" ? "#4CAF50" : "#888" }}>
                  {t.status === "done" ? "✅" : "○"}
                </Text>
              </Box>
              {t.due_date && (
                <Text size="xSmall" style={{ color: "#aaa", marginTop: 4 }}>
                  📅 {new Date(t.due_date).toLocaleDateString("vi")}
                </Text>
              )}
            </Box>
          ))
        )}
      </Box>
    </Page>
  );
}
