// ══════════════════════════════════════════════
// Food Hub — SPA Frontend Logic
// ══════════════════════════════════════════════

const App = {
    activeTab: 'recommend',
    currentUser: null,
    _currentRecipes: [],

    async init() {
        this.bindNavigation();
        this.bindRecommendForm();
        this.bindSearchForm();

        // Check if already logged in
        await this.checkAuth();
    },

    // ──── Auth ────
    async checkAuth() {
        try {
            const res = await fetch('/api/auth/me');
            const data = await res.json();
            if (data.authenticated) {
                this.currentUser = data.user;
                this.onLoginSuccess();
            } else {
                this.showAuthModal();
            }
        } catch {
            this.showAuthModal();
        }
    },

    showAuthModal() {
        document.getElementById('auth-modal').classList.add('active');
        document.getElementById('app-shell').classList.add('blurred');
        this.switchAuthMode('login');
    },

    hideAuthModal() {
        document.getElementById('auth-modal').classList.remove('active');
        document.getElementById('app-shell').classList.remove('blurred');
    },

    switchAuthMode(mode) {
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');
        const loginTab = document.getElementById('auth-tab-login');
        const signupTab = document.getElementById('auth-tab-signup');

        if (mode === 'login') {
            loginForm.style.display = 'block';
            signupForm.style.display = 'none';
            loginTab.classList.add('active');
            signupTab.classList.remove('active');
        } else {
            loginForm.style.display = 'none';
            signupForm.style.display = 'block';
            loginTab.classList.remove('active');
            signupTab.classList.add('active');
        }
        // Clear errors
        document.getElementById('auth-error').textContent = '';
    },

    async handleLogin(e) {
        e.preventDefault();
        const form = e.target;
        const btn = form.querySelector('button[type="submit"]');
        const errorEl = document.getElementById('auth-error');
        errorEl.textContent = '';
        btn.innerHTML = '<span class="spinner"></span> Logging in...';
        btn.disabled = true;

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: form.username.value,
                    password: form.password.value,
                }),
            });
            const data = await res.json();
            if (!res.ok) {
                errorEl.textContent = data.error || 'Login failed';
                return;
            }
            this.currentUser = data.user;
            this.onLoginSuccess();
            this.toast(data.message, 'success');
        } catch {
            errorEl.textContent = 'Connection error. Try again.';
        } finally {
            btn.innerHTML = 'Log In';
            btn.disabled = false;
        }
    },

    async handleSignup(e) {
        e.preventDefault();
        const form = e.target;
        const btn = form.querySelector('button[type="submit"]');
        const errorEl = document.getElementById('auth-error');
        errorEl.textContent = '';
        btn.innerHTML = '<span class="spinner"></span> Creating...';
        btn.disabled = true;

        try {
            const res = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: form.username.value,
                    password: form.password.value,
                    display_name: form.display_name.value,
                }),
            });
            const data = await res.json();
            if (!res.ok) {
                errorEl.textContent = data.error || 'Signup failed';
                return;
            }
            this.currentUser = data.user;
            this.onLoginSuccess();
            this.toast('Welcome! Your account is ready 🎉', 'success');
        } catch {
            errorEl.textContent = 'Connection error. Try again.';
        } finally {
            btn.innerHTML = 'Create Account';
            btn.disabled = false;
        }
    },

    onLoginSuccess() {
        this.hideAuthModal();
        this.updateUserUI();
        this.showTab('recommend');

        // Pre-fill diet from profile
        if (this.currentUser?.default_diet && this.currentUser.default_diet !== 'any') {
            const dietSelect = document.getElementById('diet-select');
            if (dietSelect) dietSelect.value = this.currentUser.default_diet;
        }
    },

    updateUserUI() {
        const userArea = document.getElementById('nav-user-area');
        if (!this.currentUser) {
            userArea.innerHTML = '<button class="btn-ghost" onclick="App.showAuthModal()">Log In</button>';
            return;
        }
        userArea.innerHTML = `
            <div class="nav-user" onclick="App.showTab('profile')">
                <span class="nav-avatar">${this.currentUser.avatar_emoji || '😊'}</span>
                <span class="nav-username">${this.currentUser.display_name}</span>
            </div>
        `;
    },

    async handleLogout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
        } catch {}
        this.currentUser = null;
        this.updateUserUI();
        this.showAuthModal();
        this.toast('Logged out', 'info');
    },

    // ──── Navigation ────
    bindNavigation() {
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const target = tab.dataset.tab;
                this.showTab(target);
            });
        });
    },

    showTab(tabName) {
        this.activeTab = tabName;

        // Update nav active states
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        const activeNav = document.querySelector(`.nav-tab[data-tab="${tabName}"]`);
        if (activeNav) activeNav.classList.add('active');

        // Hide all sections, show target
        document.querySelectorAll('.tab-content').forEach(s => {
            s.classList.remove('active');
            s.style.display = 'none';
        });
        const section = document.getElementById(`tab-${tabName}`);
        if (section) {
            section.style.display = 'block';
            void section.offsetWidth;
            section.classList.add('active');
        }

        // Load data for the tab
        if (tabName === 'favorites') this.loadFavorites();
        if (tabName === 'history') this.loadHistory();
        if (tabName === 'insights') this.loadInsights();
        if (tabName === 'profile') this.loadProfile();
    },

    // ──── Recommendations ────
    bindRecommendForm() {
        const form = document.getElementById('recommend-form');
        if (!form) return;
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = form.querySelector('button[type="submit"]');
            btn.innerHTML = '<span class="spinner"></span> Thinking...';
            btn.disabled = true;

            const data = {
                mood: form.mood.value,
                weather: form.weather.value,
                time: form.time.value,
                diet: form.diet.value,
            };

            try {
                const res = await fetch('/api/recommend', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                });
                if (res.status === 401) {
                    this.showAuthModal();
                    return;
                }
                const result = await res.json();
                this.renderRecommendations(result.foods);
            } catch {
                this.toast('Something went wrong. Try again!', 'error');
            } finally {
                btn.innerHTML = 'Get Recommendations 🚀';
                btn.disabled = false;
            }
        });
    },

    renderRecommendations(foods) {
        const container = document.getElementById('results-area');
        if (!foods || foods.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-emoji">😢</div>
                    <p>No matches found. Try different preferences!</p>
                </div>`;
            return;
        }

        container.innerHTML = `
            <h3 class="section-subtitle">✨ Personalized just for you</h3>
            <div class="cards-grid">
                ${foods.map((f, i) => this.foodCardHTML(f, i)).join('')}
            </div>`;
    },

    foodCardHTML(food, index) {
        const isFav = food.is_favorite;
        const maxCal = 600;
        const calPercent = Math.min((food.calories / maxCal) * 100, 100);
        const proteinPercent = Math.min((food.protein / 30) * 100, 100);
        const carbsPercent = Math.min((food.carbs / 60) * 100, 100);
        const fatPercent = Math.min((food.fat / 35) * 100, 100);

        const scoreTag = food.score !== undefined
            ? `<span class="match-badge">${Math.round((food.score / 3.8) * 100)}% match</span>`
            : '';

        return `
        <div class="food-card" style="animation-delay: ${index * 0.1}s">
            <button class="fav-btn ${isFav ? 'active' : ''}" onclick="App.toggleFavorite(${food.id}, this)" title="Toggle favorite">
                ${isFav ? '❤️' : '🤍'}
            </button>
            ${scoreTag}
            <div class="food-emoji">${food.emoji}</div>
            <div class="food-name">${food.name}</div>
            <div class="food-desc">${food.desc}</div>
            <div class="food-meta">
                <span class="meta-tag" title="Prep time">⏱ ${food.prep_time}m</span>
                <span class="meta-tag" title="Spice level">${this.spiceIcon(food.spice)}</span>
                <span class="meta-tag" title="Category">${food.category}</span>
            </div>
            <div class="nutrition-bars">
                <div class="nutri-row">
                    <span class="nutri-label">🔥 ${food.calories} cal</span>
                    <div class="nutri-bar"><div class="nutri-fill cal-fill" style="width: ${calPercent}%"></div></div>
                </div>
                <div class="nutri-row">
                    <span class="nutri-label">💪 ${food.protein}g</span>
                    <div class="nutri-bar"><div class="nutri-fill protein-fill" style="width: ${proteinPercent}%"></div></div>
                </div>
                <div class="nutri-row">
                    <span class="nutri-label">🌾 ${food.carbs}g</span>
                    <div class="nutri-bar"><div class="nutri-fill carbs-fill" style="width: ${carbsPercent}%"></div></div>
                </div>
                <div class="nutri-row">
                    <span class="nutri-label">🧈 ${food.fat}g</span>
                    <div class="nutri-bar"><div class="nutri-fill fat-fill" style="width: ${fatPercent}%"></div></div>
                </div>
            </div>
        </div>`;
    },

    spiceIcon(level) {
        const map = { none: '🧊 Mild', mild: '🌶️ Mild', medium: '🌶️🌶️ Med', hot: '🔥 Hot' };
        return map[level] || '🌶️';
    },

    // ──── Favorites ────
    async toggleFavorite(foodId, btnEl) {
        try {
            const res = await fetch(`/api/favorites/${foodId}`, { method: 'POST' });
            if (res.status === 401) { this.showAuthModal(); return; }
            const data = await res.json();
            if (data.action === 'added') {
                btnEl.classList.add('active');
                btnEl.innerHTML = '❤️';
                this.toast('Added to favorites!', 'success');
            } else {
                btnEl.classList.remove('active');
                btnEl.innerHTML = '🤍';
                this.toast('Removed from favorites', 'info');
            }
            if (this.activeTab === 'favorites') this.loadFavorites();
        } catch {
            this.toast('Could not update favorite', 'error');
        }
    },

    async loadFavorites() {
        const container = document.getElementById('favorites-content');
        container.innerHTML = '<div class="loading"><span class="spinner"></span> Loading favorites...</div>';

        try {
            const res = await fetch('/api/favorites');
            const data = await res.json();

            if (!data.favorites || data.favorites.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-emoji">💝</div>
                        <h3>No favorites yet</h3>
                        <p>Heart the foods you love from recommendations and they'll appear here!</p>
                    </div>`;
                return;
            }

            container.innerHTML = `
                <div class="cards-grid">
                    ${data.favorites.map((f, i) => this.foodCardHTML(f, i)).join('')}
                </div>`;
        } catch {
            container.innerHTML = '<div class="empty-state"><p>Could not load favorites.</p></div>';
        }
    },

    // ──── History ────
    async loadHistory() {
        const container = document.getElementById('history-content');
        container.innerHTML = '<div class="loading"><span class="spinner"></span> Loading history...</div>';

        try {
            const res = await fetch('/api/history');
            const data = await res.json();

            if (!data.history || data.history.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-emoji">📭</div>
                        <h3>No history yet</h3>
                        <p>Get some recommendations and your journey will be tracked here!</p>
                    </div>`;
                return;
            }

            const moodEmojis = { happy: '😊', sad: '😢' };
            const weatherEmojis = { sunny: '☀️', rainy: '🌧️', cold: '❄️' };
            const timeEmojis = { morning: '🌅', night: '🌙' };

            let html = `
                <div class="history-header">
                    <h3 class="section-subtitle">📜 Your Food Journey</h3>
                    <button class="clear-btn" onclick="App.clearHistory()">Clear All 🗑️</button>
                </div>
                <div class="timeline">`;

            data.history.forEach((h, i) => {
                const date = new Date(h.created_at + 'Z');
                const timeAgo = this.timeAgo(date);
                const foodTags = h.foods.map(f => `<span class="food-tag">${f.emoji} ${f.name}</span>`).join('');

                html += `
                <div class="timeline-item" style="animation-delay: ${i * 0.08}s">
                    <div class="timeline-dot"></div>
                    <div class="timeline-card">
                        <div class="timeline-meta">
                            <span>${timeAgo}</span>
                            <div class="timeline-context">
                                ${moodEmojis[h.mood] || '😊'} ${h.mood} · 
                                ${weatherEmojis[h.weather] || '☀️'} ${h.weather} · 
                                ${timeEmojis[h.time] || '🌅'} ${h.time}
                            </div>
                        </div>
                        <div class="timeline-foods">${foodTags}</div>
                    </div>
                </div>`;
            });

            html += '</div>';
            container.innerHTML = html;
        } catch {
            container.innerHTML = '<div class="empty-state"><p>Could not load history.</p></div>';
        }
    },

    async clearHistory() {
        if (!confirm('Clear all recommendation history?')) return;
        try {
            await fetch('/api/history', { method: 'DELETE' });
            this.toast('History cleared!', 'success');
            this.loadHistory();
        } catch {
            this.toast('Could not clear history', 'error');
        }
    },

    // ──── Insights / Personality ────
    async loadInsights() {
        const container = document.getElementById('insights-content');
        container.innerHTML = '<div class="loading"><span class="spinner"></span> Analyzing your taste...</div>';

        try {
            const res = await fetch('/api/insights');
            const data = await res.json();

            const moodEmojis = { happy: '😊', sad: '😢' };
            const weatherEmojis = { sunny: '☀️', rainy: '🌧️', cold: '❄️' };

            let topFoodsHTML = '';
            if (data.top_foods && data.top_foods.length > 0) {
                topFoodsHTML = `
                <div class="insight-card">
                    <h4>🏆 Your Top Foods</h4>
                    <div class="top-foods-list">
                        ${data.top_foods.map((f, i) => `
                            <div class="top-food-item">
                                <span class="top-rank">#${i + 1}</span>
                                <span class="top-emoji">${f.emoji}</span>
                                <span class="top-name">${f.name}</span>
                                <span class="top-count">${f.count}x</span>
                            </div>
                        `).join('')}
                    </div>
                </div>`;
            }

            container.innerHTML = `
                <div class="personality-card">
                    <div class="personality-emoji">${data.personality.emoji}</div>
                    <h2 class="personality-title">${data.personality.title}</h2>
                    <p class="personality-desc">${data.personality.desc}</p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">${data.total_recommendations}</div>
                        <div class="stat-label">Recommendations</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.total_favorites}</div>
                        <div class="stat-label">Favorites</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.avg_calories || '—'}</div>
                        <div class="stat-label">Avg Calories</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.top_mood ? (moodEmojis[data.top_mood] || data.top_mood) : '—'}</div>
                        <div class="stat-label">Top Mood</div>
                    </div>
                </div>

                ${topFoodsHTML}

                ${data.top_weather ? `
                <div class="insight-card">
                    <h4>🌤️ Weather Pattern</h4>
                    <p>You mostly search for food when it's <strong>${weatherEmojis[data.top_weather] || ''} ${data.top_weather}</strong></p>
                </div>` : ''}

                ${data.top_category ? `
                <div class="insight-card">
                    <h4>🍽️ Favorite Category</h4>
                    <p>You lean towards <strong>${data.top_category}</strong> foods</p>
                </div>` : ''}
            `;
        } catch {
            container.innerHTML = '<div class="empty-state"><p>Could not load insights.</p></div>';
        }
    },

    // ──── Profile ────
    async loadProfile() {
        const container = document.getElementById('profile-content');
        if (!this.currentUser) {
            container.innerHTML = '<div class="empty-state"><p>Please log in to view your profile.</p></div>';
            return;
        }

        container.innerHTML = '<div class="loading"><span class="spinner"></span> Loading profile...</div>';

        try {
            const res = await fetch('/api/auth/me');
            const data = await res.json();
            if (!data.authenticated) {
                this.showAuthModal();
                return;
            }
            this.currentUser = data.user;
            this.renderProfile(data.user);
        } catch {
            container.innerHTML = '<div class="empty-state"><p>Could not load profile.</p></div>';
        }
    },

    renderProfile(user) {
        const container = document.getElementById('profile-content');
        const avatarOptions = ['😊', '😎', '🤓', '🧑‍🍳', '🍕', '🌮', '🍣', '🎉', '🔥', '💪', '🌟', '🦊', '🐱', '🐶', '🌈', '🎨'];

        const memberDate = user.created_at ? new Date(user.created_at + 'Z').toLocaleDateString('en-US', {
            year: 'numeric', month: 'long', day: 'numeric'
        }) : 'Unknown';

        container.innerHTML = `
            <div class="profile-hero">
                <div class="profile-avatar-large">${user.avatar_emoji || '😊'}</div>
                <h2 class="profile-display-name">${user.display_name}</h2>
                <p class="profile-username">@${user.username}</p>
                <p class="profile-member-since">Member since ${memberDate}</p>
            </div>

            <div class="profile-sections">
                <div class="profile-section glass-card">
                    <h3>🎨 Avatar</h3>
                    <div class="avatar-grid">
                        ${avatarOptions.map(e => `
                            <button class="avatar-option ${e === user.avatar_emoji ? 'selected' : ''}" 
                                    onclick="App.updateAvatar('${e}', this)">${e}</button>
                        `).join('')}
                    </div>
                </div>

                <div class="profile-section glass-card">
                    <h3>✏️ Personal Info</h3>
                    <form onsubmit="App.handleProfileUpdate(event)" id="profile-info-form">
                        <div class="profile-form-grid">
                            <div class="form-group">
                                <label>Display Name</label>
                                <input type="text" name="display_name" value="${user.display_name}" required>
                            </div>
                            <div class="form-group">
                                <label>Daily Calorie Goal</label>
                                <input type="number" name="calorie_goal" value="${user.calorie_goal || 2000}" min="500" max="5000">
                            </div>
                        </div>
                        <button type="submit" class="btn-primary btn-sm">Save Changes</button>
                    </form>
                </div>

                <div class="profile-section glass-card">
                    <h3>🍽️ Food Preferences</h3>
                    <form onsubmit="App.handlePreferencesUpdate(event)" id="profile-prefs-form">
                        <div class="profile-form-grid">
                            <div class="form-group">
                                <label>Default Diet</label>
                                <select name="default_diet">
                                    <option value="any" ${user.default_diet === 'any' ? 'selected' : ''}>No Preference</option>
                                    <option value="vegetarian" ${user.default_diet === 'vegetarian' ? 'selected' : ''}>Vegetarian</option>
                                    <option value="vegan" ${user.default_diet === 'vegan' ? 'selected' : ''}>Vegan</option>
                                    <option value="gluten-free" ${user.default_diet === 'gluten-free' ? 'selected' : ''}>Gluten-Free</option>
                                    <option value="pescatarian" ${user.default_diet === 'pescatarian' ? 'selected' : ''}>Pescatarian</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Spice Preference</label>
                                <select name="spice_preference">
                                    <option value="any" ${user.spice_preference === 'any' ? 'selected' : ''}>Any</option>
                                    <option value="none" ${user.spice_preference === 'none' ? 'selected' : ''}>No Spice</option>
                                    <option value="mild" ${user.spice_preference === 'mild' ? 'selected' : ''}>Mild</option>
                                    <option value="medium" ${user.spice_preference === 'medium' ? 'selected' : ''}>Medium</option>
                                    <option value="hot" ${user.spice_preference === 'hot' ? 'selected' : ''}>Hot & Spicy</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Allergies <span class="label-hint">(comma-separated)</span></label>
                            <input type="text" name="allergies" value="${user.allergies || ''}" 
                                   placeholder="e.g., dairy, gluten, nuts, eggs, soy, shellfish">
                            <div class="allergy-chips">
                                ${['dairy', 'gluten', 'nuts', 'eggs', 'soy', 'shellfish'].map(a => {
                                    const isActive = (user.allergies || '').toLowerCase().includes(a);
                                    return `<button type="button" class="allergy-chip ${isActive ? 'active' : ''}" 
                                                onclick="App.toggleAllergyChip('${a}', this)">${a}</button>`;
                                }).join('')}
                            </div>
                        </div>
                        <button type="submit" class="btn-primary btn-sm">Save Preferences</button>
                    </form>
                </div>

                <div class="profile-section glass-card">
                    <h3>🔒 Change Password</h3>
                    <form onsubmit="App.handlePasswordChange(event)" id="password-form">
                        <div class="profile-form-grid">
                            <div class="form-group">
                                <label>Current Password</label>
                                <input type="password" name="current_password" required>
                            </div>
                            <div class="form-group">
                                <label>New Password</label>
                                <input type="password" name="new_password" required minlength="4">
                            </div>
                        </div>
                        <button type="submit" class="btn-primary btn-sm">Change Password</button>
                    </form>
                </div>

                <div class="profile-section">
                    <button class="btn-danger" onclick="App.handleLogout()">🚪 Log Out</button>
                </div>
            </div>
        `;
    },

    async updateAvatar(emoji, btnEl) {
        try {
            const res = await fetch('/api/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ avatar_emoji: emoji }),
            });
            const data = await res.json();
            if (res.ok) {
                this.currentUser = data.user;
                this.updateUserUI();
                // Update avatar selection UI
                document.querySelectorAll('.avatar-option').forEach(b => b.classList.remove('selected'));
                btnEl.classList.add('selected');
                document.querySelector('.profile-avatar-large').textContent = emoji;
                this.toast('Avatar updated!', 'success');
            }
        } catch {
            this.toast('Could not update avatar', 'error');
        }
    },

    toggleAllergyChip(allergy, chipEl) {
        chipEl.classList.toggle('active');
        // Update the text input
        const input = document.querySelector('#profile-prefs-form input[name="allergies"]');
        const activeChips = document.querySelectorAll('.allergy-chip.active');
        const allergies = Array.from(activeChips).map(c => c.textContent);
        input.value = allergies.join(', ');
    },

    async handleProfileUpdate(e) {
        e.preventDefault();
        const form = e.target;
        try {
            const res = await fetch('/api/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    display_name: form.display_name.value,
                    calorie_goal: parseInt(form.calorie_goal.value),
                }),
            });
            const data = await res.json();
            if (res.ok) {
                this.currentUser = data.user;
                this.updateUserUI();
                document.querySelector('.profile-display-name').textContent = data.user.display_name;
                this.toast('Profile updated!', 'success');
            } else {
                this.toast(data.error || 'Update failed', 'error');
            }
        } catch {
            this.toast('Connection error', 'error');
        }
    },

    async handlePreferencesUpdate(e) {
        e.preventDefault();
        const form = e.target;
        try {
            const res = await fetch('/api/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    default_diet: form.default_diet.value,
                    spice_preference: form.spice_preference.value,
                    allergies: form.allergies.value,
                }),
            });
            const data = await res.json();
            if (res.ok) {
                this.currentUser = data.user;
                // Update diet select on recommend form
                const dietSelect = document.getElementById('diet-select');
                if (dietSelect && data.user.default_diet !== 'any') {
                    dietSelect.value = data.user.default_diet;
                }
                this.toast('Preferences saved! Recommendations will adapt.', 'success');
            } else {
                this.toast(data.error || 'Update failed', 'error');
            }
        } catch {
            this.toast('Connection error', 'error');
        }
    },

    async handlePasswordChange(e) {
        e.preventDefault();
        const form = e.target;
        try {
            const res = await fetch('/api/profile/password', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_password: form.current_password.value,
                    new_password: form.new_password.value,
                }),
            });
            const data = await res.json();
            if (res.ok) {
                form.reset();
                this.toast('Password changed!', 'success');
            } else {
                this.toast(data.error || 'Failed', 'error');
            }
        } catch {
            this.toast('Connection error', 'error');
        }
    },

    // ──── Recipe Search ────
    bindSearchForm() {
        const form = document.getElementById('search-form');
        if (!form) return;
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = form.querySelector('input[name="query"]').value.trim();
            if (!query) return;

            const btn = form.querySelector('button[type="submit"]');
            btn.innerHTML = '<span class="spinner"></span> Searching...';
            btn.disabled = true;

            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                this.renderRecipes(data.recipes);
            } catch {
                this.toast('Search failed. Try again!', 'error');
            } finally {
                btn.innerHTML = '🔍 Search';
                btn.disabled = false;
            }
        });
    },

    renderRecipes(recipes) {
        const container = document.getElementById('search-results');
        if (!recipes || recipes.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-emoji">🔍</div>
                    <p>No recipes found. Try a different search!</p>
                </div>`;
            return;
        }

        container.innerHTML = `
            <div class="recipe-grid">
                ${recipes.map((r, i) => `
                    <div class="recipe-card" style="animation-delay: ${i * 0.1}s" onclick="App.showRecipeModal(${i})">
                        <div class="recipe-image" style="background-image: url('${r.image}/preview')"></div>
                        <div class="recipe-info">
                            <h4 class="recipe-name">${r.name}</h4>
                            <div class="recipe-tags">
                                <span class="recipe-tag">${r.category || 'Food'}</span>
                                <span class="recipe-tag">${r.area || 'World'}</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>`;

        this._currentRecipes = recipes;
    },

    showRecipeModal(index) {
        const recipe = this._currentRecipes?.[index];
        if (!recipe) return;

        const modal = document.getElementById('recipe-modal');
        const content = document.getElementById('recipe-modal-content');

        const ingredientsList = recipe.ingredients.map(i => `<li>${i}</li>`).join('');
        const instructions = recipe.instructions
            .split(/\r?\n/)
            .filter(s => s.trim())
            .map(s => `<p>${s}</p>`)
            .join('');

        content.innerHTML = `
            <div class="modal-header">
                <h2>${recipe.name}</h2>
                <button class="modal-close" onclick="App.closeModal()">✕</button>
            </div>
            <img src="${recipe.image}" alt="${recipe.name}" class="modal-image">
            <div class="modal-tags">
                <span class="recipe-tag">${recipe.category || ''}</span>
                <span class="recipe-tag">${recipe.area || ''}</span>
                ${recipe.video ? `<a href="${recipe.video}" target="_blank" class="recipe-tag video-tag">▶ Video</a>` : ''}
            </div>
            <div class="modal-section">
                <h3>🧾 Ingredients</h3>
                <ul class="ingredients-list">${ingredientsList}</ul>
            </div>
            <div class="modal-section">
                <h3>📝 Instructions</h3>
                <div class="instructions-text">${instructions}</div>
            </div>
        `;

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    },

    closeModal() {
        document.getElementById('recipe-modal').classList.remove('active');
        document.body.style.overflow = '';
    },

    // ──── Utilities ────
    toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add('show'));
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2500);
    },

    timeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }
};

// ──── Boot ────
document.addEventListener('DOMContentLoaded', () => App.init());
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') App.closeModal();
});
