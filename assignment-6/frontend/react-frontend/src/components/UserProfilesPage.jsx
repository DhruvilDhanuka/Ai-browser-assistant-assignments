import { useState } from "react";

export default function UserProfilesPage({ onBack }) {
  const [profile, setProfile] = useState({
    name: "Dhruvil",
    email: "dhruvil@example.com",
    phone_number: "9999999999",
    resume_text: "IIT Bombay...",
  });
  const [saved, setSaved] = useState(false);

  const handleChange = (field) => (e) => {
    setProfile({ ...profile, [field]: e.target.value });
    setSaved(false);
  };

  return (
    <div className="profile-page">
      <h2>Profile Settings</h2>

      <form>
        <div className="form-group">
          <label htmlFor="name">Name</label>
          <input id="name" value={profile.name} onChange={handleChange("name")} />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={profile.email}
            onChange={handleChange("email")}
          />
        </div>

        <div className="form-group">
          <label htmlFor="phone">Phone Number</label>
          <input
            id="phone"
            value={profile.phone_number}
            onChange={handleChange("phone_number")}
          />
        </div>

        <div className="form-group">
          <label htmlFor="resume">Resume Text</label>
          <textarea
            id="resume"
            rows={6}
            value={profile.resume_text}
            onChange={handleChange("resume_text")}
          />
        </div>

        <div className="btn-row">
          <button
            type="button"
            className="btn-save"
            onClick={() => setSaved(true)}
          >
            Save
          </button>
          {onBack && (
            <button type="button" className="btn-back" onClick={onBack}>
              Back
            </button>
          )}
        </div>

        {saved && <p className="saved-msg">Saved (mocked, not sent to backend yet).</p>}
      </form>
    </div>
  );
}
