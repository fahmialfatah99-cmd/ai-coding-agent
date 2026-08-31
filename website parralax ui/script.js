// Data Fallback Repository (diambil dari data riil GitHub fahmialfatah99-cmd)
const fallbackRepos = [
    {
        name: "ai-coding-agent",
        description: "Agen AI otonom untuk membantu coding dan pengembangan perangkat lunak secara otomatis.",
        language: "Python",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/ai-coding-agent",
        updated_at: "2026-08-31T01:41:25Z"
    },
    {
        name: "agent-alfa",
        description: "Sistem agen AI cerdas berbasis Python untuk otomatisasi tugas-tugas kompleks.",
        language: "Python",
        stargazers_count: 1,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/agent-alfa",
        updated_at: "2026-08-30T19:18:48Z"
    },
    {
        name: "imt-document-generator",
        description: "Generator dokumen otomatis untuk kebutuhan administrasi dan pelaporan.",
        language: "JavaScript",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/imt-document-generator",
        updated_at: "2026-08-29T11:53:33Z"
    },
    {
        name: "agc",
        description: "Auto Generated Content tools untuk optimasi konten web secara dinamis.",
        language: "TypeScript",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/agc",
        updated_at: "2026-08-25T03:05:24Z"
    },
    {
        name: "PDF-TOOLS",
        description: "Tools PDF Python all-in-one dengan 15+ fitur lengkap untuk manipulasi dokumen PDF.",
        language: "Python",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/PDF-TOOLS",
        updated_at: "2026-08-11T07:35:42Z"
    },
    {
        name: "pdf-tools-website",
        description: "Antarmuka web modern untuk PDF-TOOLS menggunakan TypeScript.",
        language: "TypeScript",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/pdf-tools-website",
        updated_at: "2026-08-09T08:45:01Z"
    },
    {
        name: "pt-infiniti-matriks-teknologi-",
        description: "Website profil perusahaan PT Infiniti Matriks Teknologi yang responsif dan modern.",
        language: "HTML",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/pt-infiniti-matriks-teknologi-",
        updated_at: "2026-07-31T04:34:15Z"
    },
    {
        name: "scraping",
        description: "Kumpulan tools scraping serbaguna untuk ekstraksi data dari berbagai platform.",
        language: "Python",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/scraping",
        updated_at: "2026-07-28T05:07:26Z"
    },
    {
        name: "web-scraper",
        description: "Kombinasi sempurna: Scrapy + Playwright + Proxy Rotation untuk scraping skala besar.",
        language: "Python",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/web-scraper",
        updated_at: "2026-07-27T23:40:15Z"
    },
    {
        name: "carilokermu",
        description: "Web scraping lowongan pekerjaan otomatis dari berbagai portal karir terkemuka.",
        language: "Python",
        stargazers_count: 0,
        forks_count: 3,
        html_url: "https://github.com/fahmialfatah99-cmd/carilokermu",
        updated_at: "2026-07-27T23:08:27Z"
    },
    {
        name: "website",
        description: "Website portofolio pribadi versi awal dengan desain minimalis.",
        language: "HTML",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/website",
        updated_at: "2026-07-27T05:23:13Z"
    },
    {
        name: "liquid-glass-expert.dev",
        description: "Tema liquid glass expert dengan efek glassmorphism yang memukau.",
        language: "CSS",
        stargazers_count: 1,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/liquid-glass-expert.dev",
        updated_at: "2026-07-24T04:09:48Z"
    },
    {
        name: "project-bot",
        description: "Bot otomatisasi untuk manajemen proyek dan integrasi chat platform.",
        language: "JavaScript",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/project-bot",
        updated_at: "2026-07-14T11:11:47Z"
    },
    {
        name: "alfa",
        description: "Website pribadi berbasis Astro framework dengan performa super cepat.",
        language: "Astro",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/alfa",
        updated_at: "2026-07-13T10:49:25Z"
    },
    {
        name: "website-sumur-bor",
        description: "Website landing page komersial untuk jasa pembuatan sumur bor.",
        language: "HTML",
        stargazers_count: 0,
        forks_count: 0,
        html_url: "https://github.com/fahmialfatah99-cmd/website-sumur-bor",
        updated_at: "2026-07-07T15:08:33Z"
    }
];

let repositories = [...fallbackRepos];
let activeFilter = 'all';
let searchQuery = '';

// DOM Elements
const loader = document.getElementById('loader');
const navbar = document.getElementById('navbar');
const menuBtn = document.getElementById('menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
const reposGrid = document.getElementById('repos-grid');
const searchInput = document.getElementById('search-repo');
const filterButtons = document.querySelectorAll('.filter-btn');
const emptyState = document.getElementById('empty-state');
const contactForm = document.getElementById('contact-form');

// Parallax Elements
const parallaxStars = document.getElementById('parallax-stars');
const parallaxOrb1 = document.getElementById('parallax-orb-1');
const parallaxOrb2 = document.getElementById('parallax-orb-2');
const parallaxOrb3 = document.getElementById('parallax-orb-3');
const parallaxCode1 = document.getElementById('parallax-code-1');
const parallaxCode2 = document.getElementById('parallax-code-2');
const heroContent = document.getElementById('hero-content');

// Hide Loader
window.addEventListener('load', () => {
    setTimeout(() => {
        loader.classList.add('opacity-0');
        setTimeout(() => {
            loader.style.display = 'none';
        }, 700);
    }, 500);
});

// Mobile Menu Toggle
menuBtn.addEventListener('click', () => {
    mobileMenu.classList.toggle('hidden');
    const icon = menuBtn.querySelector('i');
    if (mobileMenu.classList.contains('hidden')) {
        icon.className = 'fas fa-bars text-xl';
    } else {
        icon.className = 'fas fa-times text-xl';
    }
});

// Close mobile menu on link click
document.querySelectorAll('.mobile-nav-link').forEach(link => {
    link.addEventListener('click', () => {
        mobileMenu.classList.add('hidden');
        menuBtn.querySelector('i').className = 'fas fa-bars text-xl';
    });
});

// Navbar Scroll Effect
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.classList.remove('py-4');
        navbar.classList.add('py-2');
        navbar.querySelector('div').classList.remove('bg-brand-dark/40');
        navbar.querySelector('div').classList.add('bg-brand-dark/80', 'shadow-lg', 'border-white/20');
    } else {
        navbar.classList.remove('py-2');
        navbar.classList.add('py-4');
        navbar.querySelector('div').classList.remove('bg-brand-dark/80', 'shadow-lg', 'border-white/20');
        navbar.querySelector('div').classList.add('bg-brand-dark/40');
    }
});

// Parallax Effect on Mouse Move & Scroll
window.addEventListener('mousemove', (e) => {
    const mouseX = e.clientX / window.innerWidth - 0.5;
    const mouseY = e.clientY / window.innerHeight - 0.5;

    // Parallax Code Elements
    if (parallaxCode1) {
        parallaxCode1.style.transform = `translate(${mouseX * 40}px, ${mouseY * 40}px) rotate(-12deg)`;
    }
    if (parallaxCode2) {
        parallaxCode2.style.transform = `translate(${mouseX * -40}px, ${mouseY * -40}px) rotate(6deg)`;
    }

    // Parallax Orbs
    if (parallaxOrb1) {
        parallaxOrb1.style.transform = `translate(${mouseX * 20}px, ${mouseY * 20}px)`;
    }
    if (parallaxOrb2) {
        parallaxOrb2.style.transform = `translate(${mouseX * -30}px, ${mouseY * -30}px)`;
    }
    if (parallaxOrb3) {
        parallaxOrb3.style.transform = `translate(${mouseX * 15}px, ${mouseY * -15}px)`;
    }
});

window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;

    // Parallax Stars
    if (parallaxStars) {
        parallaxStars.style.transform = `translate3d(0, ${scrollY * 0.4}px, 0)`;
    }

    // Hero Content Fade & Translate
    if (heroContent && scrollY < window.innerHeight) {
        heroContent.style.transform = `translate3d(0, ${scrollY * 0.3}px, 0)`;
        heroContent.style.opacity = 1 - (scrollY / (window.innerHeight * 0.8));
    }
});

// Fetch Repositories from GitHub API
async function fetchGitHubRepos() {
    try {
        const response = await fetch('https://api.github.com/users/fahmialfatah99-cmd/repos?per_page=100&sort=updated');
        if (!response.ok) throw new Error('Failed to fetch');
        const data = await response.json();
        
        if (data && data.length > 0) {
            // Map API data to our structure
            repositories = data.map(repo => ({
                name: repo.name,
                description: repo.description || getFallbackDescription(repo.name),
                language: repo.language || 'Other',
                stargazers_count: repo.stargazers_count,
                forks_count: repo.forks_count,
                html_url: repo.html_url,
                updated_at: repo.updated_at
            }));
            
            // Update Stats
            updateStats();
        }
    } catch (error) {
        console.warn('Using fallback repository data due to API limit or network error.');
    }
    renderRepos();
}

function getFallbackDescription(name) {
    const found = fallbackRepos.find(r => r.name.toLowerCase() === name.toLowerCase());
    return found ? found.description : 'Proyek pengembangan perangkat lunak yang menarik.';
}

// Update Stats Cards
function updateStats() {
    const totalReposEl = document.getElementById('stat-total-repos');
    const starsEl = document.getElementById('stat-stars');
    
    if (totalReposEl) totalReposEl.textContent = repositories.length;
    
    const totalStars = repositories.reduce((sum, repo) => sum + repo.stargazers_count, 0);
    if (starsEl) starsEl.textContent = totalStars;
}

// Get Language Badge Class
function getLanguageBadgeClass(lang) {
    if (!lang) return 'badge-other';
    switch (lang.toLowerCase()) {
        case 'python': return 'badge-python';
        case 'javascript': return 'badge-javascript';
        case 'typescript': return 'badge-typescript';
        case 'html': return 'badge-html';
        case 'css': return 'badge-css';
        case 'astro': return 'badge-astro';
        default: return 'badge-other';
    }
}

// Get Language Icon
function getLanguageIcon(lang) {
    if (!lang) return 'fa-code';
    switch (lang.toLowerCase()) {
        case 'python': return 'fab fa-python';
        case 'javascript': return 'fab fa-js';
        case 'typescript': return 'fab fa-react'; // FontAwesome doesn't have TS icon, React is a good substitute or code
        case 'html': return 'fab fa-html5';
        case 'css': return 'fab fa-css3-alt';
        default: return 'fas fa-code';
    }
}

// Render Repositories to Grid
function renderRepos() {
    reposGrid.innerHTML = '';
    
    const filtered = repositories.filter(repo => {
        // Language Filter
        let matchesLang = true;
        if (activeFilter !== 'all') {
            if (activeFilter === 'html') {
                matchesLang = ['html', 'css'].includes(repo.language?.toLowerCase());
            } else {
                matchesLang = repo.language?.toLowerCase() === activeFilter;
            }
        }
        
        // Search Query
        const matchesSearch = repo.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                              (repo.description && repo.description.toLowerCase().includes(searchQuery.toLowerCase()));
        
        return matchesLang && matchesSearch;
    });

    if (filtered.length === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
        
        filtered.forEach(repo => {
            const card = document.createElement('div');
            card.className = 'glass-card glow-on-hover p-6 rounded-2xl flex flex-col justify-between h-full';
            
            const badgeClass = getLanguageBadgeClass(repo.language);
            const langIcon = getLanguageIcon(repo.language);
            
            card.innerHTML = `
                <div>
                    <div class="flex items-center justify-between mb-4">
                        <span class="px-3 py-1 rounded-full text-xs font-semibold tracking-wide ${badgeClass} flex items-center gap-1.5">
                            <i class="${langIcon}"></i> ${repo.language || 'Other'}
                        </span>
                        <span class="text-xs text-gray-500">
                            <i class="far fa-calendar-alt mr-1"></i> ${new Date(repo.updated_at).toLocaleDateString('id-ID', { year: 'numeric', month: 'short' })}
                        </span>
                    </div>
                    <h3 class="font-display text-xl font-bold text-white mb-2 hover:text-blue-400 transition-colors">
                        <a href="${repo.html_url}" target="_blank" rel="noopener noreferrer">${repo.name}</a>
                    </h3>
                    <p class="text-gray-400 text-sm leading-relaxed mb-6 line-clamp-3">
                        ${repo.description || 'Tidak ada deskripsi.'}
                    </p>
                </div>
                <div class="flex items-center justify-between pt-4 border-t border-white/5 mt-auto">
                    <div class="flex items-center space-x-4 text-gray-400 text-xs">
                        <span class="flex items-center gap-1 hover:text-yellow-400 transition-colors">
                            <i class="fas fa-star"></i> ${repo.stargazers_count}
                        </span>
                        <span class="flex items-center gap-1 hover:text-blue-400 transition-colors">
                            <i class="fas fa-code-branch"></i> ${repo.forks_count}
                        </span>
                    </div>
                    <a href="${repo.html_url}" target="_blank" rel="noopener noreferrer" class="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1 group">
                        Lihat Code <i class="fas fa-arrow-right transform group-hover:translate-x-1 transition-transform"></i>
                    </a>
                </div>
            `;
            reposGrid.appendChild(card);
        });
    }
}

// Search Input Event Listener
searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value;
    renderRepos();
});

// Filter Buttons Event Listener
filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        filterButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFilter = btn.getAttribute('data-lang');
        renderRepos();
    });
});

// Contact Form Submission
contactForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const subject = document.getElementById('subject').value;
    const message = document.getElementById('message').value;
    
    // Construct WhatsApp or Email link
    const mailtoLink = `mailto:fahmialfatah99@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(`Halo Alfa,\n\nNama saya ${name} (${email}).\n\n${message}`)}`;
    
    window.open(mailtoLink, '_blank');
    contactForm.reset();
});

// Active Navigation Link on Scroll
const sections = document.querySelectorAll('section');
const navLinks = document.querySelectorAll('.nav-link');

window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (pageYOffset >= sectionTop - 150) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').slice(1) === current) {
            link.classList.add('active');
        }
    });
});

// Initialize
fetchGitHubRepos();
updateStats();
