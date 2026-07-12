export default function ActivityPanel({ taskStatus }) {
  return (
    <div className="activity-panel">
      <h2>Live Activity</h2>
      <p className="status-text">{taskStatus}</p>
    </div>
  );
}
