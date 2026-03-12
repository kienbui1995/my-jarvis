import React, { useEffect, useState } from "react";
import { Page, Box, Text } from "zmp-ui";
import { api } from "../api";

type Event = { id: string; title: string; start_time: string; location: string };

export default function CalendarPage() {
  const [events, setEvents] = useState<Event[]>([]);
  useEffect(() => { api.listEvents().then(setEvents).catch(() => {}); }, []);

  return (
    <Page>
      <Box style={{ padding: 12 }}>
        <Text size="xLarge" bold style={{ marginBottom: 12 }}>📅 Lịch hôm nay</Text>
        {events.length === 0 ? (
          <Text style={{ color: "#888", textAlign: "center", marginTop: 40 }}>Không có sự kiện</Text>
        ) : (
          events.map((e) => (
            <Box key={e.id} style={{ background: "#2d2d44", borderRadius: 12, padding: 12, marginBottom: 8 }}>
              <Text bold>{e.title}</Text>
              <Text size="xSmall" style={{ color: "#aaa" }}>
                🕐 {new Date(e.start_time).toLocaleTimeString("vi", { hour: "2-digit", minute: "2-digit" })}
                {e.location && ` · 📍 ${e.location}`}
              </Text>
            </Box>
          ))
        )}
      </Box>
    </Page>
  );
}
