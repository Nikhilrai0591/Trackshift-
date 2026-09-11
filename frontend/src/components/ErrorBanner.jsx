export default function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div className="error-banner">
      ⚠ {message} — check that the TrackShift backend is running at the configured API URL.
    </div>
  );
}
