Fichier .github/workflows/ci.yml présent en local mais pas encore sur GitHub :
la première poussée avec GitHub CLI a été refusée tant que le jeton n’a pas la
permission « workflow ».

Pour réactiver la CI sur le dépôt distant :

1. Terminal :  gh auth refresh -h github.com -s workflow,repo
   (suivre le navigateur / code à l’écran si demandé.)

2. Puis :
   git add .github/workflows/ci.yml
   git commit -m "ci: restore GitHub Actions workflow"
   git push
