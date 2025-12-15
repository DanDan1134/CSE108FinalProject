// static/game.js
/**
 * Client-side game logic for Wordle Battle
 * Handles authentication, matchmaking, and real-time gameplay via SocketIO
 */

 let socket = null;
 let currentRoom = null;
 let currentUserId = null;
 let isMyTurn = true;
 let isPlayerOne = null;
 
 // ===== Utility Functions =====
 
 async function api(path, method = "GET", body = null) {
   try {
     const opts = {
       method,
       headers: { "Content-Type": "application/json" }
     };
     if (body) opts.body = JSON.stringify(body);
     
     console.log(`Making ${method} request to ${path}`, body);
     
     const res = await fetch(path, opts);
     console.log(`Response status: ${res.status}`);
     
     const data = await res.json();
     console.log('Response data:', data);
     
     return data;
   } catch (error) {
     console.error('API Error:', error);
     throw error;
   }
 }
 
 function showStatus(message, type = "info") {
   const statusEl = document.getElementById("status");
   statusEl.textContent = message;
   statusEl.className = `status ${type}`;
   statusEl.classList.remove("hidden");
 }
 
 function hideStatus() {
   document.getElementById("status").classList.add("hidden");
 }
 
 function formatTime(seconds) {
   const mins = Math.floor(seconds / 60);
   const secs = seconds % 60;
   return `${mins}:${secs.toString().padStart(2, '0')}`;
 }
 
 // ADDED: Detailed Stats localStorage helpers + modal rendering
 const LS_STREAK = "wb_streak";
 const LS_BEST_STREAK = "wb_best_streak";
 const LS_RECENT = "wb_recent_results";
 
 function getNum(key) {
   const v = Number(localStorage.getItem(key));
   return Number.isFinite(v) ? v : 0;
 }
 
 function setNum(key, n) {
   localStorage.setItem(key, String(n));
 }
 
 function getRecent() {
   try {
     return JSON.parse(localStorage.getItem(LS_RECENT) || "[]");
   } catch (e) {
     return [];
   }
 }
 
 function setRecent(arr) {
   localStorage.setItem(LS_RECENT, JSON.stringify(arr.slice(0, 5)));
 }
 
 function pushRecent(result, extra) {
   const arr = getRecent();
   arr.unshift({
     result,
     extra: extra || "Multiplayer",
     time: new Date().toISOString()
   });
   setRecent(arr);
 }
 
 function renderRecentModal() {
   const list = document.getElementById("dsRecent");
   if (!list) return;
 
   const items = getRecent();
 
   if (!items || items.length === 0) {
     list.innerHTML = `<div style="color:#666;">No recent games yet.</div>`;
     return;
   }
 
   list.innerHTML = items.map((it) => {
     const badge = it.result === "WIN" ? "#16a34a" : (it.result === "LOSS" ? "#dc2626" : "#6b7280");
     const when = new Date(it.time).toLocaleString();
     return `
       <div style="display:flex; justify-content:space-between; align-items:center; background:#f7f7f7; border:1px solid #eee; border-radius:10px; padding:10px;">
         <div>
           <div style="font-weight:700; color:#333;">${it.extra}</div>
           <div style="font-size:12px; color:#666;">${when}</div>
         </div>
         <div style="background:${badge}; color:white; padding:4px 10px; border-radius:999px; font-weight:800; font-size:12px;">
           ${it.result}
         </div>
       </div>
     `;
   }).join("");
 }
 
 async function openDetailedStatsModal() {
   const modal = document.getElementById("statsModal");
   if (!modal) return;
 
   // Pull server stats (same endpoint your UI uses)
   let stats = null;
   try {
     stats = await api("/stats");
   } catch (e) {
     stats = null;
   }
 
   const games = stats ? Number(stats.total_games || 0) : 0;
   const wins = stats ? Number(stats.total_wins || 0) : 0;
   const winRate = stats ? Number(stats.win_rate || 0) : (games > 0 ? Math.round((wins / games) * 100) : 0);
   const losses = Math.max(0, games - wins);
 
   const dsGames = document.getElementById("dsGames");
   const dsWins = document.getElementById("dsWins");
   const dsWinrate = document.getElementById("dsWinrate");
   const dsLosses = document.getElementById("dsLosses");
   const dsStreak = document.getElementById("dsStreak");
   const dsBestStreak = document.getElementById("dsBestStreak");
 
   if (dsGames) dsGames.textContent = String(games);
   if (dsWins) dsWins.textContent = String(wins);
   if (dsWinrate) dsWinrate.textContent = `${winRate}%`;
   if (dsLosses) dsLosses.textContent = String(losses);
 
   if (dsStreak) dsStreak.textContent = String(getNum(LS_STREAK));
   if (dsBestStreak) dsBestStreak.textContent = String(getNum(LS_BEST_STREAK));
 
   renderRecentModal();
 
   modal.classList.remove("hidden");
   modal.style.display = "flex";
 }
 
 function closeDetailedStatsModal() {
   const modal = document.getElementById("statsModal");
   if (!modal) return;
   modal.classList.add("hidden");
   modal.style.display = "none";
 }
 
 function wireDetailedStatsUI() {
   const openBtn = document.getElementById("viewDetailedStats");
   const closeBtn = document.getElementById("closeStatsModal");
   const doneBtn = document.getElementById("doneStatsModal");
   const resetBtn = document.getElementById("resetLocalStats");
   const modal = document.getElementById("statsModal");
 
   if (openBtn) {
     openBtn.addEventListener("click", async () => {
       await openDetailedStatsModal();
     });
   }
 
   if (closeBtn) closeBtn.addEventListener("click", closeDetailedStatsModal);
   if (doneBtn) doneBtn.addEventListener("click", closeDetailedStatsModal);
 
   if (modal) {
     modal.addEventListener("click", (e) => {
       if (e.target === modal) closeDetailedStatsModal();
     });
   }
 
   if (resetBtn) {
     resetBtn.addEventListener("click", () => {
       localStorage.removeItem(LS_STREAK);
       localStorage.removeItem(LS_BEST_STREAK);
       localStorage.removeItem(LS_RECENT);
       renderRecentModal();
 
       const dsStreak = document.getElementById("dsStreak");
       const dsBestStreak = document.getElementById("dsBestStreak");
       if (dsStreak) dsStreak.textContent = "0";
       if (dsBestStreak) dsBestStreak.textContent = "0";
     });
   }
 }
 
 // ===== Authentication =====
 
 // ===== Authentication =====
 
 // Wait for DOM to be ready
 document.addEventListener("DOMContentLoaded", () => {
   console.log("DOM loaded, attaching event listeners");
 
   // ADDED: wire the Detailed Stats button + modal after DOM loads
   wireDetailedStatsUI();
 
   document.getElementById("register").onclick = async () => {
     const username = document.getElementById("username").value.trim();
     const password = document.getElementById("password").value;
 
     console.log("Register button clicked", {
       username,
       passwordLength: password.length,
     });
 
     if (!username || !password) {
       showStatus("Please enter username and password", "error");
       return;
     }
 
     try {
       const res = await api("/register", "POST", { username, password });
       if (res.success) {
         showStatus("Account created! Please login", "success");
       } else {
         showStatus(res.error || "Registration failed", "error");
       }
     } catch (err) {
       console.error("Registration error:", err);
       showStatus("Network error during registration: " + err.message, "error");
     }
   };
 
   document.getElementById("login").onclick = async () => {
     const username = document.getElementById("username").value.trim();
     const password = document.getElementById("password").value;
 
     console.log("Login button clicked", {
       username,
       passwordLength: password.length,
     });
 
     if (!username || !password) {
       showStatus("Please enter username and password", "error");
       return;
     }
 
     try {
       const res = await api("/login", "POST", { username, password });
       if (res.success) {
         currentUserId = res.user_id;
         showStatus(`Welcome, ${res.username}!`, "success");
 
         // Switch UI to logged-in state
         document.getElementById("auth").classList.add("hidden");
         document.getElementById("loggedIn").classList.remove("hidden");
 
         // Load user stats
         loadUserStats();
 
         // Initialize WebSocket
         initSocket();
       } else {
         showStatus(res.error || "Login failed", "error");
       }
     } catch (err) {
       console.error("Login error:", err);
       showStatus("Network error during login: " + err.message, "error");
     }
   };
 
   document.getElementById("logout").onclick = async () => {
     try {
       await api("/logout");
       if (socket) socket.disconnect();
       socket = null;
       currentRoom = null;
       currentUserId = null;
 
       // Reset UI
       document.getElementById("auth").classList.remove("hidden");
       document.getElementById("loggedIn").classList.add("hidden");
       document.getElementById("game").classList.add("hidden");
       document.getElementById("userStats").classList.add("hidden");
 
       showStatus("Logged out successfully", "info");
     } catch (err) {
       showStatus("Error during logout", "error");
     }
   };
 
   async function loadUserStats() {
     try {
       const stats = await api("/stats");
       const statsEl = document.getElementById("userStats");
       statsEl.innerHTML = `
         <div class="stat">
           <div class="stat-value">${stats.total_games}</div>
           <div class="stat-label">Games</div>
         </div>
         <div class="stat">
           <div class="stat-value">${stats.total_wins}</div>
           <div class="stat-label">Wins</div>
         </div>
         <div class="stat">
           <div class="stat-value">${stats.win_rate}%</div>
           <div class="stat-label">Win Rate</div>
         </div>
       `;
       statsEl.classList.remove("hidden");
     } catch (err) {
       console.error("Failed to load stats:", err);
     }
   }
 
   // ===== Matchmaking =====
 
   document.getElementById("playBtn").onclick = async () => {
     try {
       const res = await api("/queue", "POST");
       if (res.queued) {
         showStatus("Searching for opponent...", "info");
         document.getElementById("playBtn").disabled = true;
       } else {
         showStatus(res.error || "Failed to join queue", "error");
       }
     } catch (err) {
       showStatus("Network error joining queue", "error");
     }
   };
 
   // ===== WebSocket Connection =====
 
   function initSocket() {
     if (socket) socket.disconnect();
 
     socket = io();
 
     socket.on("connect", () => {
       console.log("WebSocket connected");
     });
 
     socket.on("connected", (data) => {
       console.log("Connected as user:", data.user_id);
     });
 
     socket.on("not_authenticated", () => {
       showStatus("Please login first", "error");
       if (socket) socket.disconnect();
     });
 
     socket.on("match_found", (data) => {
       console.log("Match found:", data);
 
       currentRoom = data.room;
 
       // Server tells us whether we are player 1 or player 2
       if (typeof data.is_p1 === "boolean") {
         isPlayerOne = data.is_p1;
       } else {
         // Fallback if for some reason it's missing
         isPlayerOne = null;
       }
 
       showStatus("Match found! Starting game...", "success");
 
       // Join the game room
       socket.emit("join_room", { room: currentRoom });
 
       // Show game UI
       document.getElementById("game").classList.remove("hidden");
       document.getElementById("playBtn").disabled = false;
 
       // Reset game state
       resetGameUI();
     });
 
     socket.on("timer_update", (data) => {
       const timerEl = document.getElementById("timer");
       timerEl.textContent = formatTime(data.time_left);
 
       // Visual warning when time is running out
       if (data.time_left <= 30) {
         timerEl.style.color = "#d32f2f";
       } else if (data.time_left <= 60) {
         timerEl.style.color = "#f57c00";
       } else {
         timerEl.style.color = "#667eea";
       }
     });
 
     socket.on("score_update", (data) => {
       let myScore, oppScore;
 
       if (isPlayerOne === null) {
         myScore = data.p1;
         oppScore = data.p2;
       } else if (isPlayerOne) {
         myScore = data.p1;
         oppScore = data.p2;
       } else {
         myScore = data.p2;
         oppScore = data.p1;
       }
 
       document.getElementById("scoreP1").textContent = myScore;
       document.getElementById("scoreP2").textContent = oppScore;
     });
 
     socket.on("guess_feedback", (data) => {
       displayGuessFeedback(data);
     });
 
     socket.on("guess_error", (data) => {
       showStatus(data.error, "error");
     });
 
     socket.on("new_word", (data) => {
       showStatus(data.message, "success");
       setTimeout(hideStatus, 2000);
     });
 
     socket.on("game_over", (data) => {
       handleGameOver(data);
     });
 
     socket.on("player_joined", (data) => {
       console.log("Player joined:", data.username);
     });
   }
 
   // ===== Game Logic =====
 
   function resetGameUI() {
     document.getElementById("scoreP1").textContent = "0";
     document.getElementById("scoreP2").textContent = "0";
     document.getElementById("timer").textContent = "5:00";
     document.getElementById("timer").style.color = "#667eea";
     document.getElementById("feedback").innerHTML = "";
     document.getElementById("guessInput").value = "";
     document.getElementById("guessInput").disabled = false;
     document.getElementById("submitGuess").disabled = false;
   }
 
   document.getElementById("submitGuess").onclick = submitGuess;
   document
     .getElementById("guessInput")
     .addEventListener("keypress", (e) => {
       if (e.key === "Enter") submitGuess();
     });
 
   function submitGuess() {
     const input = document.getElementById("guessInput");
     const guess = input.value.trim().toUpperCase();
 
     if (guess.length !== 5) {
       showStatus("Guess must be 5 letters", "error");
       return;
     }
 
     if (!guess.match(/^[A-Z]+$/)) {
       showStatus("Guess must contain only letters", "error");
       return;
     }
 
     // Send guess to server
     socket.emit("submit_guess", {
       room: currentRoom,
       guess: guess,
     });
 
     input.value = "";
   }
 
   function displayGuessFeedback(data) {
     const feedbackEl = document.getElementById("feedback");
 
     // Create row of letter boxes
     const row = document.createElement("div");
     row.className = "feedback-row";
 
     for (let i = 0; i < data.guess.length; i++) {
       const box = document.createElement("div");
       box.className = `letter-box ${data.colors[i]}`;
       box.textContent = data.guess[i];
       row.appendChild(box);
     }
 
     // Add to top of feedback (most recent first)
     feedbackEl.insertBefore(row, feedbackEl.firstChild);
 
     // Keep only last 6 guesses visible
     while (feedbackEl.children.length > 6) {
       feedbackEl.removeChild(feedbackEl.lastChild);
     }
 
     if (data.solved) {
       showStatus("🎉 Correct! +1 point", "success");
       setTimeout(hideStatus, 2000);
     }
   }
 
   function handleGameOver(data) {
     // Disable input
     document.getElementById("guessInput").disabled = true;
     document.getElementById("submitGuess").disabled = true;
     document.getElementById("playBtn").disabled = false;
 
     const p1Score = data.final_scores?.p1 || 0;
     const p2Score = data.final_scores?.p2 || 0;
     const winnerId = data.winner_id;
 
     let myScore, oppScore;
     if (isPlayerOne === true) {
       myScore = p1Score;
       oppScore = p2Score;
     } else if (isPlayerOne === false) {
       myScore = p2Score;
       oppScore = p1Score;
     } else {
       myScore = p1Score;
       oppScore = p2Score;
     }
 
     // Update scoreboard one last time
     document.getElementById("scoreP1").textContent = myScore;
     document.getElementById("scoreP2").textContent = oppScore;
 
     let message;
     if (winnerId == null) {
       message = "It's a tie!";
     } else if (currentUserId != null && winnerId === currentUserId) {
       message = "You won! Great job!";
     } else {
       message = "You lost. Better luck next time!";
     }
 
     showStatus(
       message,
       winnerId === currentUserId ? "success" : "info"
     );
 
     // ADDED: update local streak + recent results for the Detailed Stats modal
     try {
       const didWin = (winnerId != null && currentUserId != null && winnerId === currentUserId);
       const didTie = (winnerId == null);
 
       if (didTie) {
         pushRecent("TIE", `Multiplayer (${myScore}-${oppScore})`);
         // streak unchanged on tie (common behavior)
       } else if (didWin) {
         const nextStreak = getNum(LS_STREAK) + 1;
         setNum(LS_STREAK, nextStreak);
         setNum(LS_BEST_STREAK, Math.max(getNum(LS_BEST_STREAK), nextStreak));
         pushRecent("WIN", `Multiplayer (${myScore}-${oppScore})`);
       } else {
         setNum(LS_STREAK, 0);
         pushRecent("LOSS", `Multiplayer (${myScore}-${oppScore})`);
       }
     } catch (e) {
       console.error("Failed to update local detailed stats:", e);
     }
 
     // Reload stats
     loadUserStats();
   }
 }); // End of DOMContentLoaded
 
 console.log("Game.js loaded successfully");
 