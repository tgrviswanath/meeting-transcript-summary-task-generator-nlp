import React, { useState, useEffect } from "react";
import { Container } from "@mui/material";
import Header from "./components/Header";
import MeetingPage from "./pages/MeetingPage";
import { getModels } from "./services/meetingApi";

export default function App() {
  const [models, setModels] = useState(null);

  useEffect(() => {
    getModels().then((r) => setModels(r.data)).catch(() => {});
  }, []);

  return (
    <>
      <Header models={models} />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <MeetingPage />
      </Container>
    </>
  );
}
