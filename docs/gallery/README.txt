Dossier prévu pour GitHub Pages (option 4.2 du fichier community/gallery/DEPLOY.txt).

1. Copiez votre fichier personnel :

   community\gallery\index.html   →   docs\gallery\index.html

   (même contenu : c’est la page avec votre firebaseConfig Web.)

2. Dans GitHub : Paramètres du dépôt → Pages → Source « Deploy from a branch » :
   branche « main », dossier « /docs ».

3. Votre galerie sera à l’adresse :

   https://VOTRE_USER.github.io/NOM_DU_REPO/gallery/

   (remplacez VOTRE_USER et NOM_DU_REPO.)

4. Le fichier docs/gallery/index.html contient la config Web : il est listé dans
   .gitignore comme community/gallery/index.html. Pour le pousser une fois :

   git add -f docs/gallery/index.html
   git commit -m "Pages: galerie statique"
   git push
