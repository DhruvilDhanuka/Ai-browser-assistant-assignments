import "./App.css";
import CommandBar from "./components/CommandBar.jsx";
import { useState } from "react";
import UserProfilesPage from "./components/UserProfilesPage.jsx";

function App() {
  const [userProfileSettings, setUserProfileSettings] = useState(false);

  return (
    <div>
      {!userProfileSettings ? (
        <div className="App">
          <div className="greeting">AI Browser Assistant</div>
          <CommandBar />

          <button
            className="nav-btn"
            onClick={() => {
              setUserProfileSettings(true);
            }}
          >
            User Profile Page
          </button>
        </div>
      ) : (
        <UserProfilesPage onBack={() => setUserProfileSettings(false)} />
      )}
    </div>
  );
}

export default App;
