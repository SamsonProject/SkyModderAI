/**
 * SkyModderAI User Onboarding Tour
 * Interactive guide for first-time users
 */

(function () {
    'use strict';

    // Tour steps configuration
    const tourSteps = [
        {
            id: 'welcome',
            title: 'Welcome to SkyModderAI! 🎮',
            content: 'Let us show you around! This quick tour will help you get the most out of your modding experience.',
            position: 'center',
        },
        {
            id: 'game-select',
            target: '#game-select',
            title: 'Select Your Game',
            content: 'Choose your game first! We support Skyrim (all versions), Fallout 4, Oblivion, and more. LOOT data is game-specific.',
            position: 'bottom',
        },
        {
            id: 'mod-search',
            target: '#mod-search-input',
            title: 'Search Mods',
            content: 'Type to search for mods. Click or press Enter to add them to your list. Our database uses real LOOT data.',
            position: 'bottom',
        },
        {
            id: 'mod-list-input',
            target: '#mod-list-input',
            title: 'Paste Your Mod List',
            content: 'Paste your plugins.txt, MO2 load order, or any ESP/ESM list. We support all formats automatically.',
            position: 'right',
        },
        {
            id: 'analyze-btn',
            target: '#analyze-btn',
            title: 'Analyze Now',
            content: 'Click here or press Ctrl+Enter to analyze. We\'ll find conflicts, missing requirements, and suggest fixes.',
            position: 'top',
        },
        {
            id: 'import-tools',
            target: '.input-actions-import',
            title: 'Import & Save Tools',
            content: 'Share lists, paste from clipboard, import files, load samples, or save your configurations for later.',
            position: 'top',
        },
        {
            id: 'openclaw',
            target: '[data-tab="openclaw"]',
            title: 'OpenCLAW Automation 🐾',
            content: 'Our automated modding assistant learns from your sessions, proposes improvements, and guides implementation.',
            position: 'bottom',
        },
        {
            id: 'compatibility',
            target: 'a[href="/compatibility/search"]',
            title: 'Compatibility Database',
            content: 'Search thousands of community-reported mod compatibilities. Know before you install!',
            position: 'bottom',
        },
        {
            id: 'mod-managers',
            target: 'a[href="/mod-managers"]',
            title: 'Mod Manager Integration 🔌',
            content: 'Download plugins for MO2, Vortex, or Wabbajack. Analyze conflicts without leaving your mod manager.',
            position: 'bottom',
        },
        {
            id: 'mod-authors',
            target: 'a[href="/mod-authors"]',
            title: 'Mod Author Tools 🛠️',
            content: 'Test your mod against popular mods, generate LOOT metadata, and validate requirements before release.',
            position: 'bottom',
        },
        {
            id: 'community',
            target: 'a[href="/community"]',
            title: 'Community Hub',
            content: 'Connect with other modders! Share tips, ask questions, and showcase your builds.',
            position: 'bottom',
        },
        {
            id: 'samson',
            target: '#samson-chat-toggle',
            title: 'Samson AI Assistant 🤖',
            content: 'Your AI assistant is always here to help! Click to ask questions about modding, compatibility, or anything else.',
            position: 'left',
        },
        {
            id: 'complete',
            title: 'You\'re All Set! 🎉',
            content: 'Ready to start modding? Remember: SkyModderAI is 100% free forever, built by modders for modders.',
            position: 'center',
            actions: [
                { text: 'Start Analyzing', action: 'close' },
                { text: 'Watch Video Demo', action: 'video' },
            ],
        },
    ];

    // State
    let currentStep = 0;
    let tourOverlay = null;
    let tourBox = null;

    // Check if user has completed tour
    function hasCompletedTour() {
        return localStorage.getItem('skymodderai_tour_completed') === 'true';
    }

    // Mark tour as completed
    function completeTour() {
        localStorage.setItem('skymodderai_tour_completed', 'true');
    }

    // Create tour overlay
    function createOverlay() {
        tourOverlay = document.createElement('div');
        tourOverlay.id = 'tour-overlay';
        tourOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 99998;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(tourOverlay);
    }

    // Create tour box
    function createTourBox() {
        tourBox = document.createElement('div');
        tourBox.id = 'tour-box';
        tourBox.style.cssText = `
            position: fixed;
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border: 2px solid #3b82f6;
            border-radius: 16px;
            padding: 1.5rem;
            max-width: 400px;
            z-index: 99999;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            color: #f8fafc;
            font-family: 'Inter', system-ui, sans-serif;
        `;
        document.body.appendChild(tourBox);
    }

    // Update tour box content
    function updateTourBox() {
        const step = tourSteps[currentStep];
        const total = tourSteps.length;

        tourBox.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-size: 1.25rem; color: #3b82f6;">${step.title}</h3>
                <button id="tour-close" style="background: transparent; border: none; color: #94a3b8; font-size: 1.5rem; cursor: pointer; padding: 0; line-height: 1;" aria-label="Close tour">&times;</button>
            </div>
            <p style="margin: 0 0 1.5rem 0; color: #94a3b8; line-height: 1.6;">${step.content}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #64748b; font-size: 0.875rem;">Step ${currentStep + 1} of ${total}</span>
                <div style="display: flex; gap: 0.5rem;">
                    ${currentStep > 0 ? `<button id="tour-prev" style="padding: 0.5rem 1rem; background: transparent; border: 1px solid #334155; color: #f8fafc; border-radius: 8px; cursor: pointer; font-size: 0.875rem;">← Back</button>` : ''}
                    <button id="tour-next" style="padding: 0.5rem 1.5rem; background: #3b82f6; border: none; color: #000; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.875rem;">${currentStep === total - 1 ? 'Get Started' : 'Next →'}</button>
                </div>
            </div>
            <div style="margin-top: 1rem; text-align: center;">
                <button id="tour-skip" style="background: transparent; border: none; color: #64748b; cursor: pointer; font-size: 0.75rem; text-decoration: underline;">Skip tour</button>
            </div>
        `;

        // Add event listeners
        document.getElementById('tour-close').addEventListener('click', endTour);
        document.getElementById('tour-skip').addEventListener('click', endTour);
        document.getElementById('tour-next').addEventListener('click', nextStep);

        const prevBtn = document.getElementById('tour-prev');
        if (prevBtn) {
            prevBtn.addEventListener('click', prevStep);
        }
    }

    // Position tour box
    function positionTourBox() {
        const step = tourSteps[currentStep];

        if (step.position === 'center') {
            tourBox.style.top = '50%';
            tourBox.style.left = '50%';
            tourBox.style.transform = 'translate(-50%, -50%)';
            return;
        }

        const target = document.querySelector(step.target);
        if (!target) {
            // Fallback to center if target not found
            positionTourBox({ position: 'center' });
            return;
        }

        const rect = target.getBoundingClientRect();
        const boxRect = tourBox.getBoundingClientRect();

        let top, left;

        switch (step.position) {
            case 'bottom':
                top = rect.bottom + 10;
                left = rect.left + (rect.width / 2) - (boxRect.width / 2);
                break;
            case 'right':
                top = rect.top + (rect.height / 2) - (boxRect.height / 2);
                left = rect.right + 10;
                break;
            case 'left':
                top = rect.top + (rect.height / 2) - (boxRect.height / 2);
                left = rect.left - boxRect.width - 10;
                break;
            default:
                top = rect.bottom + 10;
                left = rect.left;
        }

        // Keep within viewport
        top = Math.max(10, Math.min(top, window.innerHeight - boxRect.height - 10));
        left = Math.max(10, Math.min(left, window.innerWidth - boxRect.width - 10));

        tourBox.style.top = `${top}px`;
        tourBox.style.left = `${left}px`;
        tourBox.style.transform = 'none';
    }

    // Next step
    function nextStep() {
        if (currentStep < tourSteps.length - 1) {
            currentStep++;
            updateTourBox();
            setTimeout(positionTourBox, 100);
        } else {
            endTour();
        }
    }

    // Previous step
    function prevStep() {
        if (currentStep > 0) {
            currentStep--;
            updateTourBox();
            setTimeout(positionTourBox, 100);
        }
    }

    // End tour
    function endTour() {
        completeTour();
        if (tourOverlay) tourOverlay.remove();
        if (tourBox) tourBox.remove();

        // Show thank you message
        showThankYou();
    }

    // Show thank you message
    function showThankYou() {
        const toast = document.createElement('div');
        toast.id = 'tour-toast';
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 100000;
            animation: slideIn 0.3s ease;
        `;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.5rem;">✅</span>
                <div>
                    <strong>Tour completed!</strong>
                    <p style="margin: 0; font-size: 0.875rem; opacity: 0.9;">Happy modding! 🎮</p>
                </div>
            </div>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Reset tour (for testing or restart)
    function resetTour() {
        localStorage.removeItem('skymodderai_tour_completed');
    }

    // Expose reset function globally for console access
    window.resetSkyModderAITour = resetTour;

    // Start tour
    function startTour() {
        currentStep = 0;
        createOverlay();
        createTourBox();
        updateTourBox();
        setTimeout(positionTourBox, 100);
    }

    // Initialize
    function init() {
        // Connect to header tour button
        const headerTrigger = document.getElementById('tour-trigger');
        if (headerTrigger) {
            headerTrigger.addEventListener('click', startTour);
        }

        // Auto-start for first-time users with a beautiful welcome modal
        if (!hasCompletedTour()) {
            setTimeout(() => {
                showWelcomeModal();
            }, 1500);
        }
    }

    // Show beautiful welcome modal for first-time users
    function showWelcomeModal() {
        const modal = document.createElement('div');
        modal.id = 'welcome-modal';
        modal.style.cssText = `
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 999999;
            animation: fadeIn 0.3s ease;
        `;

        modal.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                border: 1px solid rgba(6, 182, 212, 0.3);
                border-radius: 20px;
                padding: 3rem;
                max-width: 500px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                animation: slideUp 0.4s ease;
            ">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎮</div>
                <h2 style="
                    font-size: 2rem;
                    margin-bottom: 1rem;
                    background: linear-gradient(135deg, #06b6d4, #a855f7);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                ">Welcome to SkyModderAI!</h2>
                <p style="
                    color: #94a3b8;
                    font-size: 1.1rem;
                    line-height: 1.6;
                    margin-bottom: 2rem;
                ">
                    Find mod conflicts in seconds. Stop crashing to desktop. 
                    Built by modders, for modders. <strong>100% free forever.</strong>
                </p>
                <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                    <button id="welcome-tour-btn" style="
                        background: linear-gradient(135deg, #06b6d4, #a855f7);
                        color: white;
                        border: none;
                        padding: 1rem 2rem;
                        border-radius: 10px;
                        font-size: 1rem;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.15s;
                    ">🎯 Take Quick Tour</button>
                    <button id="welcome-skip-btn" style="
                        background: transparent;
                        color: #94a3b8;
                        border: 1px solid #334155;
                        padding: 1rem 2rem;
                        border-radius: 10px;
                        font-size: 1rem;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.15s;
                    ">Skip, I'll Explore</button>
                </div>
                <p style="
                    color: #64748b;
                    font-size: 0.875rem;
                    margin-top: 1.5rem;
                ">
                    You can always start the tour later from the navigation menu.
                </p>
            </div>
        `;

        document.body.appendChild(modal);

        // Add animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes slideUp {
                from { transform: translateY(30px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        // Event handlers
        document.getElementById('welcome-tour-btn').addEventListener('click', () => {
            modal.remove();
            startTour();
        });

        document.getElementById('welcome-skip-btn').addEventListener('click', () => {
            modal.remove();
            completeTour();
            showThankYou();
        });

        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
                completeTour();
            }
        });
    }

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
