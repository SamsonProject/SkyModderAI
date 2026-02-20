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
            id: 'analyze',
            target: '[data-tab="analyze"]',
            title: 'Analyze Your Mod List',
            content: 'Paste your mod list here and get AI-powered conflict detection, load order optimization, and compatibility insights.',
            position: 'bottom',
        },
        {
            id: 'community',
            target: '[data-tab="community"]',
            title: 'Community Hub',
            content: 'Connect with other modders! Share tips, ask questions, and showcase your builds.',
            position: 'bottom',
        },
        {
            id: 'build-list',
            target: '[data-tab="build-list"]',
            title: 'Build a List',
            content: 'Generate custom mod lists based on your preferences. AI-powered recommendations tailored to your playstyle.',
            position: 'bottom',
        },
        {
            id: 'library',
            target: '[data-tab="library"]',
            title: 'Your Library',
            content: 'Save and organize your mod configurations. Access them anytime and share with friends.',
            position: 'bottom',
        },
        {
            id: 'shopping',
            target: 'a[href="/shopping"]',
            title: 'Shopping Marketplace 🛒',
            content: 'Browse gaming gear, custom mods, and more from verified businesses. Support the community while you shop!',
            position: 'bottom',
        },
        {
            id: 'business',
            target: 'a[href="/business"]',
            title: 'Business Community 🏢',
            content: 'Have a modding-related business? Get listed for free and reach thousands of modders.',
            position: 'bottom',
        },
        {
            id: 'samson',
            target: '#samson-chat-toggle',
            target: '#agent-toggle',
            title: 'Meet Samson AI 🤖',
            content: 'Your AI assistant is always here to help! Click to ask questions about modding, compatibility, or anything else.',
            position: 'right',
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

    // Start tour
    function startTour() {
        currentStep = 0;
        createOverlay();
        createTourBox();
        updateTourBox();
        setTimeout(positionTourBox, 100);
    }

    // Show tour trigger button
    function showTourTrigger() {
        const trigger = document.createElement('button');
        trigger.id = 'tour-trigger';
        trigger.innerHTML = '🎯 Take Tour';
        trigger.style.cssText = `
            position: fixed;
            bottom: 100px;
            left: 20px;
            padding: 0.75rem 1.25rem;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            border: none;
            border-radius: 9999px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.875rem;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            z-index: 9999;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        `;
        trigger.addEventListener('mouseenter', () => {
            trigger.style.transform = 'scale(1.05)';
            trigger.style.boxShadow = '0 6px 20px rgba(59, 130, 246, 0.6)';
        });
        trigger.addEventListener('mouseleave', () => {
            trigger.style.transform = 'scale(1)';
            trigger.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.4)';
        });
        trigger.addEventListener('click', startTour);
        document.body.appendChild(trigger);
    }

    // Initialize
    function init() {
        // Always show tour trigger for easy access
        showTourTrigger();

        // Auto-start for first-time users after a short delay
        if (!hasCompletedTour()) {
            setTimeout(() => {
                const startNow = confirm('Welcome to SkyModderAI! Would you like a quick tour of the features?');
                if (startNow) {
                    startTour();
                } else {
                    completeTour();
                }
            }, 2000);
        }
    }

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
