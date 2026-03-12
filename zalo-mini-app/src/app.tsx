/**
 * App entry — Zalo OAuth login + routing.
 */
import React, { useEffect, useState } from "react";
import { App, ZMPRouter, SnackbarProvider } from "zmp-ui";
import { getAccessToken, authorize } from "zmp-sdk";
import { api, setToken } from "./api";

import ChatPage from "./pages/index";
import TasksPage from "./pages/tasks";
import CalendarPage from "./pages/calendar";
import NotificationsPage from "./pages/notifications";

export default function MyApp() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        // Get Zalo access token
        const { accessToken } = await getAccessToken({});
        // Exchange for our JWT
        const { access_token } = await api.zaloLogin(accessToken);
        setToken(access_token);
        setReady(true);
      } catch {
        // Fallback: request authorization
        authorize({
          scopes: ["scope.userInfo"],
          success: () => window.location.reload(),
          fail: () => {},
        });
      }
    })();
  }, []);

  if (!ready) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#888" }}>
        Đang đăng nhập...
      </div>
    );
  }

  return (
    <App>
      <SnackbarProvider>
        <ZMPRouter>
          <ChatPage path="/" />
          <TasksPage path="/tasks" />
          <CalendarPage path="/calendar" />
          <NotificationsPage path="/notifications" />
        </ZMPRouter>
      </SnackbarProvider>
    </App>
  );
}
