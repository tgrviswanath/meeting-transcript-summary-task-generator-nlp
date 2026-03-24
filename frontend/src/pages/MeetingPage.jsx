import React, { useState, useRef } from "react";
import {
  Box, Button, CircularProgress, Alert, Typography, Paper,
  Chip, TextField, Divider, Tabs, Tab, Table, TableBody,
  TableCell, TableHead, TableRow, LinearProgress, IconButton, Tooltip,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { transcribeAudio, processTranscript } from "../services/meetingApi";

const SAMPLE_TRANSCRIPT = `Good morning everyone. Let's get started with our weekly sync.

John: I'll finish the API documentation by Friday. Sarah, can you review it before the client demo?

Sarah: Sure, I'll review it by Thursday afternoon. Also, I need to update the deployment scripts for the new environment. I'll handle that by end of day Wednesday.

Mike: The database migration is still pending. I'll complete it by next Monday. John, please make sure the staging environment is ready before that.

John: Got it, I'll set up staging by this Wednesday.

Sarah: One more thing - we need to schedule a security audit. Mike, can you reach out to the security team this week?

Mike: Yes, I'll contact them by tomorrow.

Manager: Great. Let's also make sure the Q3 report is submitted by end of this month. Sarah, can you take the lead on that?

Sarah: Absolutely, I'll start drafting it today.`;

const PRIORITY_COLOR = { High: "error", Medium: "warning", Low: "success" };

export default function MeetingPage() {
  const [tab, setTab] = useState(0);
  const [transcript, setTranscript] = useState(SAMPLE_TRANSCRIPT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef();

  const handleAudioUpload = async (file) => {
    if (!file) return;
    setTranscribing(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await transcribeAudio(fd);
      setTranscript(r.data.transcript);
      setTab(1); // switch to transcript tab
    } catch (e) {
      setError(e.response?.data?.detail || "Transcription failed.");
    } finally {
      setTranscribing(false);
    }
  };

  const handleProcess = async () => {
    if (!transcript.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const r = await processTranscript(transcript);
      setResult(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Processing failed.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => navigator.clipboard.writeText(text);

  return (
    <Box>
      {/* Input tabs: Audio Upload | Paste Transcript */}
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="🎙 Upload Audio" />
        <Tab label="📄 Paste Transcript" />
      </Tabs>

      {tab === 0 && (
        <Paper
          variant="outlined"
          onClick={() => fileRef.current.click()}
          onDrop={(e) => { e.preventDefault(); handleAudioUpload(e.dataTransfer.files[0]); }}
          onDragOver={(e) => e.preventDefault()}
          sx={{
            p: 4, mb: 2, textAlign: "center", cursor: "pointer", borderStyle: "dashed",
            "&:hover": { bgcolor: "action.hover" },
          }}
        >
          <input ref={fileRef} type="file" hidden
            accept=".mp3,.mp4,.wav,.m4a,.ogg,.flac,.webm"
            onChange={(e) => handleAudioUpload(e.target.files[0])} />
          {transcribing
            ? <Box>
                <CircularProgress size={28} sx={{ mb: 1 }} />
                <Typography color="text.secondary">Transcribing with Whisper…</Typography>
              </Box>
            : <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1 }}>
                <UploadFileIcon color="action" fontSize="large" />
                <Box>
                  <Typography>Drag & drop or click to upload audio</Typography>
                  <Typography variant="caption" color="text.secondary">
                    MP3, MP4, WAV, M4A, OGG, FLAC, WEBM
                  </Typography>
                </Box>
              </Box>
          }
        </Paper>
      )}

      {tab === 1 && (
        <TextField
          fullWidth multiline rows={8}
          label="Meeting Transcript"
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          sx={{ mb: 2 }}
          size="small"
          helperText={`${transcript.split(/\s+/).filter(Boolean).length} words`}
        />
      )}

      <Button
        variant="contained" size="large" onClick={handleProcess}
        disabled={!transcript.trim() || loading}
        startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
        sx={{ mb: 2 }}
      >
        {loading ? "Processing…" : "Analyze Meeting"}
      </Button>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {result && (
        <Box>
          <Divider sx={{ mb: 3 }} />

          {/* Summary */}
          <Paper variant="outlined" sx={{ p: 2.5, mb: 3 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
              <Typography variant="subtitle1" fontWeight="bold">📋 Meeting Summary</Typography>
              <Tooltip title="Copy summary">
                <IconButton size="small" onClick={() => copyToClipboard(result.summary)}>
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            <Typography variant="body2" sx={{ lineHeight: 1.8 }}>{result.summary}</Typography>
            <Box sx={{ mt: 1 }}>
              <Chip label={`${result.word_count} words in transcript`} size="small" variant="outlined" />
            </Box>
          </Paper>

          {/* Tasks table */}
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            ✅ Action Items ({result.tasks.length})
          </Typography>
          {result.tasks.length === 0
            ? <Alert severity="info">No action items detected.</Alert>
            : (
              <Paper variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: "grey.50" }}>
                      <TableCell>#</TableCell>
                      <TableCell>Task</TableCell>
                      <TableCell>Owner</TableCell>
                      <TableCell>Deadline</TableCell>
                      <TableCell>Priority</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.tasks.map((t, i) => (
                      <TableRow key={i} hover>
                        <TableCell>{i + 1}</TableCell>
                        <TableCell sx={{ maxWidth: 320 }}>
                          <Typography variant="body2">{t.task}</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={t.owner} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">{t.deadline}</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={t.priority}
                            size="small"
                            color={PRIORITY_COLOR[t.priority] || "default"}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>
            )
          }
        </Box>
      )}
    </Box>
  );
}
