<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->

<a id="readme-top"></a>

<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Unlicense License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="assets/imgs/icona.jpg" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Flexin Backupper</h3>

  <p align="center">
    Backup flexin data to a central server
    <br />
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

The latest version of Flexin software adopted a new database engine and decorporated the images from a db table.
This pushed us toward the need of a new backup software.
This software is useful for two needs.

- Backup of the data in case of Flexin PC breakdown
- Gather data for historian software

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Built With

[![Next][python]][python-url]

<p>version: 3.14.0</p>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

### Prerequisites

- Install python

### Installation

1. Create a new project folder
2. Via shell move to the project folder and there create a virtual environment, it will contain all the libraries

```sh
#Create a venv in current folder
python -m venv .venv
```

3. Clone the repo

   ```sh
   git clone https://github.com/BagnatiUmberto/FlexinBackupper.git
   ```

4. Run the virtual environment

5. Via shell move to the requirements.txt folder and install the libraries
   ```sh
   pip install -r requirements.txt
   ```
6. Via shell move to the "code/server" folder and run
   ```sh
   py main.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Usage

### Database backup

<p>Once the program has started you will see a window like this</p>
<img src="assets/imgs/readme_imgs/start.png" alt="Logo" height="180">
<p>Click on "add flexin", the settings window will open</p>
<img src="assets/imgs/readme_imgs/settings.png" alt="Logo" height="180">
<p>Input the database connection parameters and press save</p>
<p>If everything went fine a local database for storing the reels and defect data will be created and the bakcup process will start</p>

### Images backup

<p>
This application will automatically start a server that listens for client's connections.
The server will manage the backup of the images. It receive zip files from clients containing the images, unzip them and move the images to the desired location. The destination folder for the images can be set in the config file at "%appdata%/Local/FlexinBackupper/CONFIG/general_config.ini"
</p>
<p>
In this architecture the flexin Ipc play the client role. The client program has to be installed on it and run.
</p>

<p>The client configuration file</p>

```
[SERVER]
#IP = 192.168.10.173
IP = 127.0.0.1
PORT = 6392

[CLIENT]
IMGS_DIR = ../../Img_copy

[FLEXIN]
NAME = Flexin1
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->

## Roadmap

- [x] Add Changelog
- [x] Add back to top links
- [ ] Add Additional Templates w/ Examples
- [ ] Add "components" document to easily copy & paste sections of the readme
- [ ] Multi-language Support
  - [ ] Chinese
  - [ ] Spanish

See the [open issues](https://github.com/othneildrew/Best-README-Template/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->

## License

Distributed under the Unlicense License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

Umberto Bagnati - u.bagnati@electronicsystems.it

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=for-the-badge
[contributors-url]: https://github.com/othneildrew/Best-README-Template/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/othneildrew/Best-README-Template.svg?style=for-the-badge
[forks-url]: https://github.com/othneildrew/Best-README-Template/network/members
[stars-shield]: https://img.shields.io/github/stars/othneildrew/Best-README-Template.svg?style=for-the-badge
[stars-url]: https://github.com/othneildrew/Best-README-Template/stargazers
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/othneildrew/Best-README-Template/issues
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/othneildrew
[product-screenshot]: ./assets/imgs/readme_imgs/Cover.png
[settings-screenshot]: ./assets/imgs/readme_imgs/settings.png
[python]: https://www.python.org/static/community_logos/python-logo-generic.svg
[python-url]: https://www.python.org/
