import { useState, useEffect } from "react";
import { Modal } from "./Modal";
import { useSettings } from "../../context/SettingsContext";
import {
  TableColor,
  AnimationSpeed,
  TABLE_COLOR_MAP,
  TABLE_COLOR_LABELS,
  ANIMATION_SPEED_LABELS,
} from "../../types";
import {
  getVersion,
  checkForUpdate,
  applyUpdate,
  getUpdateStatus,
  getSharePreview,
  shareData,
  downloadCommunityData,
} from "../../services/api";
import type {
  VersionInfo,
  UpdateCheckResponse,
  UpdateStatusResponse,
  SharePreviewResponse,
} from "../../services/api";
import styles from "../../styles/settings.module.css";

interface SettingsModalProps {
  onClose: () => void;
}

const TABLE_COLOR_OPTIONS: TableColor[] = [
  TableColor.CLASSIC_GREEN,
  TableColor.NAVY_BLUE,
  TableColor.BURGUNDY,
  TableColor.DARK_WOOD,
  TableColor.SLATE_GRAY,
  TableColor.EMERALD,
  TableColor.MIDNIGHT_BLACK,
  TableColor.TEAL_OCEAN,
  TableColor.ROYAL_PURPLE,
  TableColor.COFFEE_BROWN,
];

const ANIMATION_SPEED_OPTIONS: AnimationSpeed[] = [
  AnimationSpeed.SLOW,
  AnimationSpeed.MEDIUM,
  AnimationSpeed.FAST,
];

export function SettingsModal({ onClose }: SettingsModalProps) {
  const { settings, updateTableColor, updateAnimationSpeed } = useSettings();

  return (
    <Modal title="Settings" onClose={onClose}>
      <div className={styles.settingsContent}>
        <TableColorPicker selected={settings.tableColor} onSelect={updateTableColor} />
        <AnimationSpeedPicker selected={settings.animationSpeed} onSelect={updateAnimationSpeed} />
        <CommunityDataSection />
        <UpdateSection />
      </div>
    </Modal>
  );
}

// --- Table Color Picker ---

interface TableColorPickerProps {
  selected: TableColor;
  onSelect: (color: TableColor) => void;
}

function TableColorPicker({ selected, onSelect }: TableColorPickerProps) {
  return (
    <div className={styles.settingsSection}>
      <span className={styles.sectionTitle}>Table Color</span>
      <div className={styles.colorGrid}>
        {TABLE_COLOR_OPTIONS.map((color) => {
          const optionClass = [
            styles.colorOption,
            selected === color ? styles.selected : "",
          ].filter(Boolean).join(" ");

          const colorValues = TABLE_COLOR_MAP[color];

          return (
            <div key={color} className={optionClass} onClick={() => onSelect(color)}>
              <div
                className={styles.colorSwatch}
                style={{
                  background: `radial-gradient(circle at 35% 35%, ${colorValues.light}, ${colorValues.base}, ${colorValues.dark})`,
                }}
              />
              <span className={styles.colorLabel}>{TABLE_COLOR_LABELS[color]}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Animation Speed Picker ---

interface AnimationSpeedPickerProps {
  selected: AnimationSpeed;
  onSelect: (speed: AnimationSpeed) => void;
}

function AnimationSpeedPicker({ selected, onSelect }: AnimationSpeedPickerProps) {
  return (
    <div className={styles.settingsSection}>
      <span className={styles.sectionTitle}>Animation Speed</span>
      <div className={styles.speedGroup}>
        {ANIMATION_SPEED_OPTIONS.map((speed) => {
          const optionClass = [
            styles.speedOption,
            selected === speed ? styles.selected : "",
          ].filter(Boolean).join(" ");

          return (
            <div key={speed} className={optionClass} onClick={() => onSelect(speed)}>
              {ANIMATION_SPEED_LABELS[speed]}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Community Data Section ---

function CommunityDataSection() {
  const { settings, updateShareData } = useSettings();
  const [preview, setPreview] = useState<SharePreviewResponse | null>(null);
  const [shareStatus, setShareStatus] = useState<"idle" | "sharing" | "done" | "error">("idle");
  const [downloadStatus, setDownloadStatus] = useState<"idle" | "downloading" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    getSharePreview().then(setPreview).catch(() => {});
  }, []);

  const handleShare = async () => {
    setShareStatus("sharing");
    setMessage("");
    try {
      const result = await shareData();
      setShareStatus(result.success ? "done" : "error");
      setMessage(result.message);
    } catch {
      setShareStatus("error");
      setMessage("Could not connect to server");
    }
  };

  const handleDownload = async () => {
    setDownloadStatus("downloading");
    setMessage("");
    try {
      const result = await downloadCommunityData();
      setDownloadStatus(result.success ? "done" : "error");
      setMessage(result.message);
      if (result.success) {
        // Refresh preview counts
        getSharePreview().then(setPreview).catch(() => {});
      }
    } catch {
      setDownloadStatus("error");
      setMessage("Could not download community data");
    }
  };

  return (
    <div className={styles.settingsSection}>
      <span className={styles.sectionTitle}>Community Data</span>
      <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", margin: "4px 0 8px" }}>
        <input
          type="checkbox"
          checked={settings.shareData}
          onChange={(event) => updateShareData(event.target.checked)}
          style={{ width: "16px", height: "16px", cursor: "pointer" }}
        />
        <span style={{ fontSize: "0.85rem" }}>Help improve AI by sharing my game decisions</span>
      </label>
      <div className={styles.versionInfo} style={{ marginBottom: "8px" }}>
        Anonymized numeric features only — no names or personal data
      </div>
      {preview && (
        <div className={styles.versionInfo}>
          Local: {preview.total} examples ({preview.human_bid_decisions + preview.human_play_decisions} from you)
        </div>
      )}
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
        <button
          className={styles.updateButton}
          onClick={handleShare}
          disabled={shareStatus === "sharing" || !preview || preview.total === 0}
          style={{ flex: 1 }}
        >
          {shareStatus === "sharing" ? "Sharing..." : shareStatus === "done" ? "Shared!" : "Share Data"}
        </button>
        <button
          className={styles.updateButton}
          onClick={handleDownload}
          disabled={downloadStatus === "downloading"}
          style={{ flex: 1 }}
        >
          {downloadStatus === "downloading" ? "Downloading..." : downloadStatus === "done" ? "Downloaded!" : "Get Community Data"}
        </button>
      </div>
      {message && (
        <div className={styles.updateStatus} style={{
          color: (shareStatus === "error" || downloadStatus === "error")
            ? "var(--color-danger)"
            : "var(--color-success)",
        }}>
          {message}
        </div>
      )}
    </div>
  );
}

// --- Update Section ---
//
// UI states (local to this component, distinct from the server's update
// state machine):
//   idle              — initial, after a benign result, or after a fresh check
//   checking          — calling /check
//   update-available  — /check returned a newer SHA on origin/main
//   updating          — /apply succeeded; we're polling /status
//   success           — /status returned success; app is about to restart
//   up-to-date        — either /check or /status confirmed no change
//   error             — anything that went wrong
//
// We poll /api/update/status every 1.5s while updating so the user sees
// before -> after SHA on success, or the tail of the build log on failure.
// The old flow just said "Updating..." and then either restarted (often
// silently into the same version) or hung — there was no way to tell what
// actually happened.

type UpdateStatus =
  | "idle"
  | "checking"
  | "up-to-date"
  | "update-available"
  | "updating"
  | "success"
  | "error";

const STATUS_POLL_MS = 1500;

function UpdateSection() {
  const [status, setStatus] = useState<UpdateStatus>("idle");
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [updateInfo, setUpdateInfo] = useState<UpdateCheckResponse | null>(null);
  const [serverStatus, setServerStatus] = useState<UpdateStatusResponse | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getVersion().then(setVersion).catch(() => {});
  }, []);

  // Poll the backend's update state while an update is in flight.
  useEffect(() => {
    if (status !== "updating") return;

    let cancelled = false;
    const poll = async () => {
      try {
        const result = await getUpdateStatus();
        if (cancelled) return;
        setServerStatus(result);

        if (result.state === "success") {
          setStatus("success");
          setMessage(result.message);
          // The backend will kill the process in ~2.5s; the helper shell
          // then opens the freshly-built bundle. Refresh the version label
          // optimistically so the user sees the new SHA before restart.
          if (result.after_sha) {
            setVersion((current) =>
              current
                ? { ...current, git_sha: result.after_sha! }
                : { git_sha: result.after_sha!, build_date: null },
            );
          }
        } else if (result.state === "up_to_date") {
          setStatus("up-to-date");
          setMessage(result.message);
        } else if (result.state === "error") {
          setStatus("error");
          setMessage(result.message);
        }
      } catch {
        // Server may be restarting after a successful update — that's the
        // expected end state, so swallow this. If status was already
        // "success" the user will see the success message until the new
        // app's UI loads.
      }
    };

    poll();
    const handle = window.setInterval(poll, STATUS_POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(handle);
    };
  }, [status]);

  const handleCheck = async () => {
    setStatus("checking");
    setMessage("");
    try {
      const result = await checkForUpdate();
      setUpdateInfo(result);
      if (result.error) {
        setStatus("error");
        setMessage(result.error);
      } else if (result.update_available) {
        setStatus("update-available");
      } else if (result.ci_status === "failing") {
        setStatus("up-to-date");
        setMessage("A new version is being tested. Check back soon.");
      } else {
        setStatus("up-to-date");
        setMessage("You're on the latest version.");
      }
    } catch {
      setStatus("error");
      setMessage("Could not reach server");
    }
  };

  const handleUpdate = async () => {
    setStatus("updating");
    setMessage("Pulling latest changes and rebuilding...");
    setServerStatus(null);
    try {
      const result = await applyUpdate();
      if (!result.success) {
        setStatus("error");
        setMessage(result.message);
      }
    } catch {
      setStatus("error");
      setMessage("Update failed");
    }
  };

  const buttonLabel = {
    idle: "Check for Updates",
    checking: "Checking...",
    "up-to-date": "Check Again",
    "update-available": "Update Now",
    updating: "Updating...",
    success: "Restarting...",
    error: "Retry",
  }[status];

  const isDisabled = status === "checking" || status === "updating" || status === "success";

  const handleClick = () => {
    if (status === "update-available") {
      handleUpdate();
    } else {
      handleCheck();
    }
  };

  return (
    <div className={styles.settingsSection}>
      <span className={styles.sectionTitle}>Updates</span>
      <button
        className={styles.updateButton}
        onClick={handleClick}
        disabled={isDisabled}
      >
        {buttonLabel}
      </button>
      {status === "up-to-date" && (
        <div className={styles.updateStatus} style={{ color: "var(--color-success)" }}>
          {message || "You're on the latest version"}
        </div>
      )}
      {status === "update-available" && updateInfo && (
        <div className={styles.updateStatus}>
          New version available: {updateInfo.latest_sha}
          {updateInfo.latest_message && <> — {updateInfo.latest_message}</>}
        </div>
      )}
      {status === "updating" && (
        <div className={styles.updateStatus} style={{ color: "var(--color-accent)" }}>
          {message}
        </div>
      )}
      {status === "success" && serverStatus && (
        <div className={styles.updateStatus} style={{ color: "var(--color-success)" }}>
          Updated {serverStatus.before_sha} → {serverStatus.after_sha}. Restarting...
        </div>
      )}
      {status === "error" && message && (
        <div className={styles.updateStatus} style={{ color: "var(--color-danger)", whiteSpace: "pre-wrap" }}>
          {message}
        </div>
      )}
      {version && (
        <div className={styles.versionInfo}>
          Version: {version.git_sha}{version.build_date ? ` · Built ${version.build_date.split("T")[0]}` : ""}
        </div>
      )}
    </div>
  );
}

