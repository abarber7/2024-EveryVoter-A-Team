function createShootingStar() {
    let shootingStar = document.createElement('div');
    shootingStar.className = 'shooting-star';
    shootingStar.style.top = Math.random() * window.innerHeight + 'px';
    shootingStar.style.left = Math.random() * window.innerWidth + 'px';
    shootingStar.style.animationDelay = Math.random() * 2 + 's'; // Increase frequency of stars

    document.querySelector('.shooting-stars').appendChild(shootingStar);

    setTimeout(() => {
        shootingStar.remove();
    }, 2000); // Adjust to match animation duration
}

// Increase frequency of star creation
setInterval(createShootingStar, 500);
