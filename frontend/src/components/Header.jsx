import React from "react";
import { AppBar, Toolbar, Typography, Chip, Box } from "@mui/material";
import MicIcon from "@mui/icons-material/Mic";

export default function Header({ models }) {
  return (
    <AppBar position="static" color="primary">
      <Toolbar sx={{ justifyContent: "space-between" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <MicIcon />
          <Typography variant="h6" fontWeight="bold">
            Meeting Transcript Analyzer
          </Typography>
        </Box>
        {models && (
          <Box sx={{ display: "flex", gap: 1 }}>
            <Chip label={`🎙 ${models.whisper_model}`} size="small"
              sx={{ bgcolor: "rgba(255,255,255,0.2)", color: "white" }} />
            <Chip label={`📝 BART`} size="small"
              sx={{ bgcolor: "rgba(255,255,255,0.2)", color: "white" }} />
            <Chip label={`🤖 ${models.llm_model}`} size="small"
              sx={{ bgcolor: "rgba(255,255,255,0.2)", color: "white" }} />
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}
